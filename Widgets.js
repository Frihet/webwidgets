var webwidgets_values = new Object();

function webwidgets_event_handler () {
 if (typeof event === 'undefined')
  type = 'load';
 else
  type = event.type;
 for (handler in this.webwidgets_events['on' + type])
  this.webwidgets_events['on' + type][handler]();
}

function webwidgets_add_event_handler (obj, eventName, key, fn) {
 if (typeof obj.webwidgets_events == 'undefined')
  obj.webwidgets_events = new Object();
 if (typeof obj.webwidgets_events['on' + eventName] == 'undefined')
  obj.webwidgets_events['on' + eventName] = new Object();
 obj.webwidgets_events['on' + eventName][key] = fn
 obj['on' + eventName] = webwidgets_event_handler;
}


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

webwidgets_add_event_handler(window, 'load', 'iefix', webwidgets_iefix_load);
