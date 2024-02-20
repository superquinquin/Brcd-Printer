


async function sendJob() {
    let barcode = document.getElementById("txtInput").value;
    let qty = document.getElementById("qtyInput").value;
    payload = {
        method: "POST", 
        mode: "cors", 
        cache: "no-cache", 
        credentials: "same-origin", 
        headers: {"Content-Type": "application/json"}, 
        redirect: "follow", 
        referrerPolicy: "no-referrer",
        body: JSON.stringify({"barcode":barcode, "qty":qty})
    };
    const response = await fetch("./job", payload);
    const data = await response.json();
    new MsgFactory("msg-box", data.type, data.msg, true, 3000, 1000);
    if (data.type == "ok") {
        document.getElementById("txtInput").value = "";
        document.getElementById("qtyInput").value = 1;
    }
    HideHints();
}    


async function findHint(event) {
    // all softkeys chars == 229
    if ((event.keyCode >= 48 && event.keyCode <= 57) || (event.keyCode >= 65 && event.keyCode <= 90) || event.keyCode == 8 || event.keyCode == 46 || event.keyCode == 229) {
        let input = document.getElementById("txtInput").value;
        if (input == "") {
            ClearHints();
            HideHints();
            return;
        }
        
        payload = {
            method: "POST", 
            mode: "cors", 
            cache: "no-cache", 
            credentials: "same-origin", 
            headers: {"Content-Type": "application/json"}, 
            redirect: "follow", 
            referrerPolicy: "no-referrer",
            body: JSON.stringify({"input":input})
        };
        const response = await fetch("./getHint", payload);
        const data = await response.json();
        if (data.type == "err") {
            return;
        }
        ClearHints();
        PopulateHint(data);
        ShowHints();
    }
}

document.getElementById("txtInput").addEventListener("keyup", (event) => {findHint(event)});
document.getElementById("txtInput").addEventListener("touchend", (event) => {findHint(event)});




function selectHint(elm) {
    document.getElementById("txtInput").value = elm.getAttribute("value");
    HideHints();
}

function PopulateHint(data) {
    let type = data._type;
    let input = data.input;
    if (data.results) {
        data.results.forEach( (payload) => {
            new Hint(input, type, payload);
        });
    }
}

function ShowHints() {
    document.getElementById("hint-container").style.display = "block";
}

function HideHints() {
    document.getElementById("hint-container").style.display = "none";
}

function ClearHints() {
    let container = document.getElementById("hint-container");
    container.innerHTML = "";
}

class Hint {
    constructor(input, type, payload) {
        let container = document.getElementById("hint-container");
        let frame = this._buildframe(payload);
        frame.appendChild(this._build_main_element(type, input, payload));
        frame.appendChild(this._build_sec_element(type, payload));
        container.appendChild(frame);
    }


    _buildframe(payload) {
        let frame = document.createElement("div");
        frame.classList.add("hint", "border");
        frame.setAttribute("value", payload.barcode)
        frame.setAttribute("onclick", "selectHint(this)")
        return frame;
    }

    _build_main_element(type, input, payload) {
        let elm = document.createElement("p");
        elm.classList.add("main");

        if (type == "barcode") {
            var highlighted = this._highlightSubString(input, payload.barcode);
        } else {
            var highlighted = this._highlightSubString(input, payload.name);
        }
        elm.innerHTML = highlighted;
        return elm;
    }

    _build_sec_element(type, payload) {
        let elm = document.createElement("p");
        elm.classList.add("sec");
        if (type == "barcode") {
            elm.innerText = payload.name;
        } else {
            elm.innerText = payload.barcode;
        }
        return elm;
    }

    _highlightSubString(input, value) {
        return value.toLowerCase().replace(input.toLowerCase(), "<strong>"+input.toLowerCase()+"</strong>");
    }
}

class MsgFactory {
    constructor(containerId, mtype, msg, fade=false, sleep=0, speed=0) {
        const container = document.getElementById(containerId);

        let frame = this.buildFrame(mtype);
        frame.appendChild(this.buildSymbol(mtype));
        frame.appendChild(this.buildMsg(msg));
        frame.appendChild(this.buildExit());

        let node = container.appendChild(frame);
        if (fade) {
            this.fadeOut(node, sleep, speed);
        }
    }


    buildFrame(mtype) {
        let frame = document.createElement("div");
        frame.classList.add(mtype, "msg-container");
        frame.style.opacity = 100;
        return frame;
    }

    buildSymbol(mtype) {
        let elm = document.createElement('img');
        elm.classList.add("msg-symbol","msg-comp"); 
        elm.setAttribute("src","/static/misc/"+mtype+".png");
        return elm;
    }

    buildMsg(msg) {
        let elm = document.createElement("p");
        elm.classList.add("msg", "msg-comp");
        elm.innerHTML = msg;
        return elm;
    }

    buildExit() {
        let elm = document.createElement("div");
        elm.classList.add("quit-container");
        
        let btn = document.createElement("button");
        btn.classList.add("msg-quit", "msg-comp");
        btn.setAttribute("onclick", "closeMsg(this)");
        btn.innerText = "x";

        elm.appendChild(btn);
        return elm;   
    }

    async fadeOut(node, slp, speed) {
        await sleep(slp);
        node.style.transition = speed+'ms';
        node.style.opacity = 0;
        await sleep(speed);
        node.remove();
    }
}

function closeMsg(elm) {
    let box = elm.parentElement.parentElement;
    box.remove();
}

function sleep (time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}