

(function($) {
    /* "use strict" */
	
 var dzChartlist = function(){
	
	var donutChart2 = function(){
		$("span.donut3").peity("donut", {
			width: "120",
			height: "120"
		})
	}
	var donutChart4 = function(){
		$("span.donut4").peity("donut", {
			width: "160",
			height: "160"
		})
	}
	
	
	
	/* Function ============ */
		return {
			init:function(){
            },
			
			
			load:function(){
                donutChart2();
                donutChart4();
			},
			
			resize:function(){
			}
		}
	
	}();

	
		
	jQuery(window).on('load',function(){
		setTimeout(function(){
			dzChartlist.load();
		}, 1000); 
		
	});

     

})(jQuery);