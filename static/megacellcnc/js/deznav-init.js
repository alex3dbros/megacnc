
"use strict"

var dzSettingsOptions = {};

function getUrlParams(dParam) 
	{
		var dPageURL = window.location.search.substring(1),
			dURLVariables = dPageURL.split('&'),
			dParameterName,
			i;

		for (i = 0; i < dURLVariables.length; i++) {
			dParameterName = dURLVariables[i].split('=');

			if (dParameterName[0] === dParam) {
				return dParameterName[1] === undefined ? true : decodeURIComponent(dParameterName[1]);
			}
		}
	}

(function($) {
	
	"use strict"
	
	/* var direction =  getUrlParams('dir');
	
	if(direction == 'rtl')
	{
        direction = 'rtl'; 
    }else{
        direction = 'ltr'; 
    } */
	
	dzSettingsOptions = {
		typography: "poppins",
		version: "dark",
		layout: "vertical",
		primary: "color_1",
		headerBg: "color_4",
		navheaderBg: "color_4",
		sidebarBg: "color_1",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};

	
	
	
	new dzSettings(dzSettingsOptions); 

	jQuery(window).on('resize',function(){
        /*Check container layout on resize */
		///alert(dzSettingsOptions.primary);
        dzSettingsOptions.containerLayout = $('#container_layout').val();
        /*Check container layout on resize END */
        
		new dzSettings(dzSettingsOptions); 
	});
	
})(jQuery);