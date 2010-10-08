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
                if (data === "<p>success</p>") {
                    if (redirect != "none") { window.location = redirect; }
                    else { return false; }
                }
                form.data('formstatus','ready');
                form.html(data);
                $('#loading').hide();
                form.fadeTo(duration,1);
            }
        });
    }
}
