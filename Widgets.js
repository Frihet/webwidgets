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
 buttons = document.getElementsByTagName('button');
 for (i = buttons.length - 1; i >= 0; i--)
  if (buttons[i] != event.srcElement)
   buttons[i].parentNode.removeChild(buttons[i]);
 buttons = document.getElementsByTagName('input');
 for (i = buttons.length - 1; i >= 0; i--)
  if (buttons[i].type == "submit")
   if (buttons[i] != event.srcElement)
    buttons[i].parentNode.removeChild(buttons[i]);
 event.srcElement.innerText = webwidgets_values['fieldValue_' + event.srcElement.id];
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

webwidgets_add_event_handler(window, 'load', 'webwidgets_iefix', webwidgets_iefix_load);
