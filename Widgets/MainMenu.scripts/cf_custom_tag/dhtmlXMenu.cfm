<cfsetting enablecfoutputonly="yes">


<cfparam name="attributes.style" default="">
<cfparam name="attributes.context" default="">
<cfparam name="attributes.mode" default="classic">
<cfparam name="attributes.type" default="a2">
	<cfset attributes.type=lcase(attributes.type)>
	<cfset attributes.mode=lcase(attributes.mode)>
		
<cfparam name="attributes.withoutImages" default="">
<cfparam name="attributes.mixedImages" default="1">



<cfif attributes.mode eq "alpha" or attributes.mode eq "classic">
	<cfparam name="attributes.width" default="100%">
	<cfparam name="attributes.height" default="">
<cfelse>
	<cfparam name="attributes.width" default="">
	<cfparam name="attributes.height" default="">	
</cfif>
<cfparam name="attributes.align" default="left">


<cfparam name="attributes.menuname" default="t#left(replace(CreateUUID(),'-','','All'),15)#">
<cfparam name="attributes.title" default=" ">

<cfparam name="attributes.JSPath" default="js/">
<cfparam name="attributes.CSSPath" default="css/">
<cfparam name="attributes.iconsPath" default="imgs/">


<cfparam name="attributes.onSelect" default="">
<cfparam name="attributes.xmlFile" default="">

<cfif not ThisTag.HasEndTag>
   <cfabort showerror="You need to supply a closing &lt;CF_dhtmlXMenu&gt; tag.">
</cfif>

<cfif ThisTag.ExecutionMode is "End">
	<cfsavecontent variable="menuOutput">
		<cfoutput>
		<cfif not isDefined("request.dhtmlXMenuScriptsInserted")>
			<link rel="STYLESHEET" type="text/css" href="#attributes.CSSPath#dhtmlXMenu.css">
			<script  src="#attributes.JSPath#dhtmlXCommon.js"></script>
			<script  src="#attributes.JSPath#dhtmlXProtobar.js"></script>				
			<script  src="#attributes.JSPath#dhtmlXMenuBar.js"></script>	
			<cfset request.dhtmlXMenuScriptsInserted=1>
		</cfif>
		<cfif len(attributes.context)>
			<link rel="STYLESHEET" type="text/css" href="#attributes.CSSPath#Context.css">
			<script  src="#attributes.JSPath#dhtmlXMenuBar_cp.js"></script>	
			<script>
				function drawMenu#attributes.menuname#(){
					#attributes.menuname#=new dhtmlXContextMenuObject("#attributes.width#","#attributes.height#","#attributes.title#");				
					#attributes.menuname#.menu.setGfxPath("#attributes.iconsPath#");
					<cfif len(attributes.xmlFile)>
					#attributes.menuname#.menu.loadXML("#attributes.xmlFile#");		
					</cfif>
					<cfif len(attributes.onSelect)>
						#attributes.menuname#.setContextMenuHandler(#attributes.onSelect#);
					</cfif>		
					<cfif Len(Trim(ThisTag.GeneratedContent))>
						#attributes.menuname#.menu.loadXMLString("<?xml version='1.0'?><menu <cfif len(attributes.withoutImages)>withoutImages='1'</cfif> <cfif len(attributes.mixedImages)>mixedImages='1'</cfif> mode='#attributes.mode#' type='#attributes.type#'  name='#attributes.title#' height='#attributes.height#'  width='#attributes.width#' disableType='image' absolutePosition='auto' menuAlign='#attributes.align#'>#replace(replace(ThisTag.GeneratedContent,'"',"'","ALL"),"#chr(13)##chr(10)#","","ALL")#</menu>")
					</cfif>
				}
				drawMenu#attributes.menuname#();					
			</script>			
		<cfelse>
			<div id="menubox_#attributes.menuname#" style="width:#attributes.width#; height:#attributes.height#;  #attributes.style#"></div>
			<script>
				function drawMenu#attributes.menuname#(){
				
				#attributes.menuname#=new dhtmlXMenuBarObject('menubox_#attributes.menuname#',"100%","100%","#attributes.title#",<cfif attributes.mode eq "alpha" or attributes.mode eq "classic">0<cfelse>1</cfif>);
				<cfif len(attributes.onSelect)>
					#attributes.menuname#.setOnClickHandler("#attributes.onSelect#");
				</cfif>
					#attributes.menuname#.setGfxPath("#attributes.iconsPath#");
				<cfif len(attributes.xmlFile)>
					#attributes.menuname#.loadXML("#attributes.xmlFile#")
				</cfif>
				<cfif Len(Trim(ThisTag.GeneratedContent))>
					#attributes.menuname#.loadXMLString("<?xml version='1.0'?><menu <cfif len(attributes.withoutImages)>withoutImages='1'</cfif> <cfif len(attributes.mixedImages)>mixedImages='1'</cfif> mode='#attributes.mode#' type='#attributes.type#'  name='#attributes.title#' height='#attributes.height#'  width='#attributes.width#' disableType='image' absolutePosition='auto' menuAlign='#attributes.align#'>#replace(replace(ThisTag.GeneratedContent,'"',"'","ALL"),"#chr(13)##chr(10)#","","ALL")#</menu>")
				</cfif>
					#attributes.menuname#.showBar();		
				};
				drawMenu#attributes.menuname#();					
			</script>
		</cfif>					
		
		</cfoutput>
	</cfsavecontent>

    <cfset ThisTag.GeneratedContent = menuOutput>
</cfif>
<cfsetting enablecfoutputonly="no">