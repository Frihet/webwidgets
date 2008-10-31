var webwidgets_values = new Object();
var webwidgets_delayed_event_handlers = new Object();

function webwidgets_event_handler(event1) {
 if (typeof event1 === 'undefined')
  event1 = event;
 type = event1.type;
 for (handler in this.webwidgets_events['on' + type])
  this.webwidgets_events['on' + type][handler]();
}

function webwidgets_add_event_handler(obj, eventName, key, fn) {
 if (typeof obj.webwidgets_events == 'undefined')
  obj.webwidgets_events = new Object();
 if (typeof obj.webwidgets_events['on' + eventName] == 'undefined')
  obj.webwidgets_events['on' + eventName] = new Object();
 obj.webwidgets_events['on' + eventName][key] = fn
 obj['on' + eventName] = webwidgets_event_handler;
}


function webwidgets_add_event_handler_once_loaded(objId, eventName, key, fn) {
 handler = new Object();
 handler.objId = objId;
 handler.eventName = eventName;
 handler.key = key;
 handler.fn = fn;
 webwidgets_delayed_event_handlers[objId + ':' + eventName + ':' + key] = handler;
}

function webwidgets_delayed_load() {
 for (handlerName in webwidgets_delayed_event_handlers) {
  handler = webwidgets_delayed_event_handlers[handlerName];
  webwidgets_add_event_handler(
   document.getElementById(handler.objId),
   handler.eventName,
   handler.key,
   handler.fn);
 }
}
webwidgets_add_event_handler(window, 'load', 'webwidgets_delayed', webwidgets_delayed_load);




function webwidgets_submit_button_iefix() {
  if (window.navigator.userAgent.indexOf ( "MSIE " ) <= 0)
    return;
  
  buttons = document.getElementsByTagName('button');
  for (i = buttons.length - 1; i >= 0; i--) {
    if (buttons[i] != event.srcElement) {
      buttons[i].disabled = true;
    }
  }
  
  buttons = document.getElementsByTagName('input');
  for (i = buttons.length - 1; i >= 0; i--) {
    if (buttons[i].type == "submit" && buttons[i] != event.srcElement) {
      buttons[i].disabled = true;      
    }
  }
  
  if (event.srcElement.tagName.toLowerCase() == "button"
      || (   event.srcElement.tagName.toLowerCase() == "input"
	     && event.srcElement.type.toLowerCase() == "submit")) {
    event.srcElement.innerText = webwidgets_values['field_value_' + event.srcElement.id];
  }
}


function webwidgets_iefix_load() {
 buttons = document.getElementsByTagName('button');
 for (i = 0; i < buttons.length; i++)
  buttons[i].onclick = webwidgets_submit_button_iefix;
 buttons = document.getElementsByTagName('input');
 for (i = 0; i < buttons.length; i++)
  if (buttons[i].type == "submit")
   buttons[i].onclick = webwidgets_submit_button_iefix;
}

if (window.navigator.userAgent.indexOf ( "MSIE " ) > 0){
 webwidgets_add_event_handler(window, 'load', 'webwidgets_iefix', webwidgets_iefix_load);
}


function selectParent(element, selector) {
 while (element.parentNode) {
  if (element.match(selector))
   return element;
  element = element.parentNode;
 }
}

function webwidgets_click_expand(event) {
 clickExpand = selectParent(event.target, '.click-expand');
 content = clickExpand.select('.content')[0];

 if (content.style.display == "block")
  content.style.display = "none";
 else
  content.style.display = "block";

 event.cancelBubble = true;
 if (event.stopPropagation) event.stopPropagation();
}

function webwidgets_click_expand_load() {
 click_expands = $$('.click-expand');
 for (i = 0; i < click_expands.length; i++)
  click_expands[i].onclick = webwidgets_click_expand;
}

webwidgets_add_event_handler(window, 'load', 'webwidgets_click_expand', webwidgets_click_expand_load);


function webwidgets_js_dialog(event) {
 clickExpand = selectParent(event.target, '.js-dialog');

 if ($(event.target).match('.expand')) {
  clickExpand.select('.foot > .expand')[0].style.display = "none";
  clickExpand.select('.foot > .collapse')[0].style.display = "inline";
  clickExpand.select('.body .content')[0].style.display = "block";

 } else if ($(event.target).match('.collapse')) {
  clickExpand.select('.foot > .expand')[0].style.display = "inline";
  clickExpand.select('.foot > .collapse')[0].style.display = "none";
  clickExpand.select('.body .content')[0].style.display = "none";

 } else if ($(event.target).match('.hide')) {
  clickExpand.style.display = "none";
 }

 event.cancelBubble = true;
 if (event.stopPropagation) event.stopPropagation();
}

function webwidgets_js_dialog_load() {
 js_dialogs = $$('.js-dialog');
 for (i = 0; i < js_dialogs.length; i++)
  js_dialogs[i].onclick = webwidgets_js_dialog;
}

webwidgets_add_event_handler(window, 'load', 'webwidgets_js_dialog', webwidgets_js_dialog_load);
