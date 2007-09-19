var webwidgets_values = new Object();

function webwidgets_submit_button() {
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

function webwidgets_load() {
 buttons = document.getElementsByTagName('button');
 for (i = 0; i < buttons.length; i++)
  buttons[i].onclick = webwidgets_submit_button;
 buttons = document.getElementsByTagName('input');
 for (i = 0; i < buttons.length; i++)
  if (buttons[i].type == "submit")
   buttons[i].onclick = webwidgets_submit_button;
}

window.onload = webwidgets_load;
