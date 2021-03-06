/* Imgee plugin
Dependencies: Jquery>=1.8.3, Jquery PostMessage plugin (jquery.ba-postmessage.js)
*/

function putURL(imgee_holder, imgname, settings){
    var image_url = settings['imgee_url'] + settings['file_endpoint'] + imgname;
    if (settings['size']){
        image_url += '?size=' + settings['size'];
    }
    $(imgee_holder).val(image_url);
}

(function($) {
    $.fn.imgee = function(options){
        $.fn.imgee.defaults = {
            imgee_url: 'http://images.hasgeek.com/',
            button_desc: 'Select or Upload Image',
            label: $(this).data('img-label'),
            profile: $(this).data('profile'),
            size: $(this).data('img-size'),
            popup_endpoint: '/popup', // enpoint for pop_up_gallery in Imgee
            file_endpoint: '/embed/file/',
            callback: putURL,
            debug: false,
            // pop-up window attributes
            window_name: 'imgee',
            window_height: 600,
            window_width: 800,
            window_resizable: true,
            window_scrollbars: true,
        };

        var settings = $.extend({}, $.fn.imgee.defaults, options);
        settings['imgee_host'] = settings.imgee_url.match('.*://.*')[0];
        setup.apply(this, [settings]);
        recv_messages_from(this, settings.imgee_host, settings);
    };

    function recv_messages_from(imgee_holder, from, options){
        $.receiveMessage(
            function(e){
                if (options.debug){
                    debug('Recieved from ' + options.imgee_host + ' :' + e.data);
                }
                options.callback.apply(this, [imgee_holder, e.data, options]);
        }, from);
    }

    function setup(options){
        var imgee_block = $("<div class='imgee-block' />")
            .prepend("<div class='imgee-container' />")
            .prepend("<div class='image-holder' />")
            .append("<div class='button-holder' />")
            .prepend('<button id="select_imgee" type="button">' + options.button_desc + '</button>');
        $(this).after(imgee_block);
        $(this).siblings('div.imgee-block')
                .find('button#select_imgee')
                .click(function(){
            openPopupWindow(options);
        });
    }

    function openPopupWindow(options){
        // remove trailing slash in imgee_url, if exists
        var url = options.imgee_url.replace(/\/$/, '');

        var props = 'width=' + options.window_width;
            props += ',height=' + options.window_height;
        if (options.window_resizable)
            props += ',resizable'
        if (options.window_scrollbars)
            props += ',scrollbars'
        if (options.profile){
            url += '/' + options.profile + options.popup_endpoint;
        }else{
            url+= options.popup_endpoint;
        }
        url += '?from=' + window.location.href;
        if (options.label){
            url += '&label=' + options.label;
        }
        win = window.open(url, options.window_name, props);
        return win;
    }
        
    function debug(obj) {
        if (window.console && window.console.log)
            window.console.log(obj);
    };
    
})(jQuery);

/* Example Usage */
/*
<html>
<head>
<script type="text/javascript" src="static/jquery.min.js"></script>
<script type="text/javascript" src="static/jquery.ba-postmessage.js"></script>
<script type="text/javascript" src="static/imgee.js"></script>
<script>
$(function(){
    $(".imgee_holder").imgee({
            'imgee_url': 'http://0.0.0.0:4500/<profile>/popup',
             debug:true
    });
});
</script>
</head>
<body>
    <div class='imgee_holder'></div>
</body>
</html>
*/
