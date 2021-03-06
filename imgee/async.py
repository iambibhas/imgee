import redis
from celery import Task
import celery.states
from celery.result import AsyncResult, EagerResult
from flask import url_for, redirect, current_app, make_response
import time

import imgee
from imgee import app
from imgee.models import db
import storage, utils

def now_in_secs():
    return int(time.time())

def get_taskid(funcname, imgname):
    return "{f}:{n}".format(f=funcname, n=imgname)


class BaseTask(celery.Task):
    abstract = True
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        # even if the task fails remove task_id so that on next request the task is executed.
        imgee.registry.remove(task_id)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        super(BaseTask, self).on_failure(exc, task_id, args, kwargs, einfo)
        db.session.rollback()


class TaskRegistry(object):
    def __init__(self, name='default', connection=None):
        self.connection = redis.from_url(connection) if connection else None
        self.name = name
        self.key = 'imgee:registry:%s' % name

    def set_connection(self, connection=None):
        connection = connection or app.config.get('REDIS_URL')
        self.connection = redis.from_url(connection)

    def add(self, taskid):
        self.connection.sadd(self.key, taskid)

    def remove(self, taskid):
        self.connection.srem(self.key, taskid)

    def __contains__(self, taskid):
        return self.connection.sismember(self.key, taskid)

    def keys_starting_with(self, exp):
        return [k for k in self.connection.smembers(self.key) if k.startswith(exp)]

    def is_queued_for_deletion(self, imgname):
        taskid = get_taskid('delete', imgname)
        return taskid in self


def queueit(funcname, *args, **kwargs):
    """
    Execute `funcname` function with `args` and `kwargs` if CELERY_ALWAYS_EAGER is True.
    Otherwise, check if it's queued already in `TaskRegistry`. If not, add it to `TaskRegistry` and queue it.
    """

    func = getattr(storage, funcname)
    taskid = get_taskid(funcname, kwargs.pop('taskid'))
    if app.config.get('CELERY_ALWAYS_EAGER'):
        return func(*args, **kwargs)
    else:
        # check it in the registry.
        if taskid in imgee.registry:
            job = AsyncResult(taskid, app=imgee.celery)
            if job.status == celery.states.SUCCESS:
                return job.result
        else:
            # add in the registry and enqueue the job
            imgee.registry.add(taskid)
            job = func.apply_async(args=args, kwargs=kwargs, task_id=taskid)
        return job


def loading():
    """
    Returns the `LOADING_IMG` as the content of the response.
    """
    with open(app.config.get('LOADING_IMG')) as loading_img:
        response = make_response(loading_img.read())
        response.headers['Content-Type'] = utils.get_file_type(loading_img)
        return response


class StillProcessingException(Exception):
    pass


def get_async_result(job):
    """
    If the result of the `job` is not yet ready, return that else raise StillProcessingException.
    If the input is `str` instead, return that.
    """
    if isinstance(job, AsyncResult):
        if job.status == celery.states.SUCCESS:
            return job.result
        else:
            img_name = job.task_id.split(':')[1]
            raise StillProcessingException(img_name)
    elif isinstance(job, (str, unicode)):
        return job
