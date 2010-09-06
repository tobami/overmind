function confirmation(message, target) {
    var answer = confirm(message);
    if (answer){
        window.location = target;
    }
}
