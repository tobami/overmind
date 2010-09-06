function confirmation(message, target) {
    var answer = confirm(message);
    if (answer){
        window.location = target;
    }
}

function ajaxSubmit(form) {
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
        console.log('kuku');
        //send data to server for validation
        $.ajax({
            url: formUrl,
            type: formMethod,
            data: formData,
            success:function(data){
                if (data === "<p>success</p>") { 
                    window.location = "/overview/";
                }
                form.data('formstatus','ready');
                form.html(data);
                $('#loading').hide();
                form.fadeTo(duration,1);
            }
        });
    }
}