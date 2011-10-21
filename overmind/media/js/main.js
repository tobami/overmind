$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});


function confirmation(message, target) {
    var answer = confirm(message);
    if (answer){
        window.location = target;
    }
}

function ajaxSubmit(form, redirect) {
    var toOpacity = 0.3;
    var duration = 100;
    //check the form is not currently submitting
    if(form.data('formstatus') !== 'submitting'){
        //setup variables
        formData = form.serialize();
        formUrl = form.attr('action');
        formMethod = form.attr('method');
        
        //add status data to form
        form.data('formstatus','submitting');
        
        //transition
        form.fadeTo(duration, toOpacity);
        $('#loading').show();
        
        //send data to server for validation
        $.ajax({
            url: formUrl,
            type: formMethod,
            data: formData,
            success:function(data){
                $('#loading').hide();
                if (data === "<p>success</p>") {
                    if (redirect) { window.location = redirect; }
                }
                form.data('formstatus','ready');
                form.html(data);
                form.fadeTo(duration,1);
            }
        });
    }
}
