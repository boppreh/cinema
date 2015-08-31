function post(url, param) {
    var r = new XMLHttpRequest();
    if (param !== undefined) {
        r.open('POST', url + "/" + param, true);
    } else {
        r.open('POST', url, true);
    }
    r.send();
}

