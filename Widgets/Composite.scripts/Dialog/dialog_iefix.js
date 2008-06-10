if (window.navigator.userAgent.indexOf ( "MSIE " ) > 0){
    function webwidgets_dialog_iefix(){
	var elem = document.getElementsByTagName('div')[0].id;

	var eMain = document.getElementById(elem);
	var eHead = document.getElementById(elem).firstChild;
	var eBody = document.getElementById(elem).firstChild.nextSibling;
	var eFoot = document.getElementById(elem).firstChild.nextSibling.nextSibling;

	if(eHead.className != "" && eBody.className != "" && eFoot.className != ""){
	    eMain.className = 'dialog-iefix';
	    eHead.className = 'dialog-head-iefix';
	    eBody.className = 'dialog-body-iefix';
	    eFoot.className = 'dialog-foot-iefix';
	}
    }
    
    webwidgets_add_event_handler(window, 'load', 'webwidgets_dialog_iefix', webwidgets_dialog_iefix);
}

