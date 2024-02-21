

(function($) {
    /* "use strict" */
	
 var dzChartlist = function(){
	
	var screenWidth = $(window).width();
	let draw = Chart.controllers.line.__super__.draw; //draw shadow
	
	
	
	
	
	var projectChart = function(){
		var options = {
			series: [30, 40, 20, 10],
         chart: {
			type: 'donut',
			width: 250,
		},
       plotOptions: {
			pie: {
			  donut: {
				size: '90%',
				labels: {
					show: true,
					name: {
						show: true,
						offsetY: 12,
					},
					value: {
						show: true,
						fontSize: '24px',
						fontFamily:'Arial',
						fontWeight:'500',
						offsetY: -17,
					},
					total: {
						show: true,
						fontSize: '11px',
						fontWeight:'500',
						fontFamily:'Arial',
						label: 'Total projects',
					   
						formatter: function (w) {
						  return w.globals.seriesTotals.reduce((a, b) => {
							return a + b
						  }, 0)
						}
					}
				}
			  }
			}
		},
		 legend: {
                show: false,
            },
		 colors: ['#FF9F00', 'var(--primary)', '#3AC977','#FF5E5E'],
			labels: ["Compete", "Pending", "Not Start"],
			dataLabels: {
				enabled: false,
			},
        };
		var chartBar1 = new ApexCharts(document.querySelector("#projectChart"), options);
		chartBar1.render();
	 
	}
 
	/* Function ============ */
		return {
			init:function(){
			},
			
			
			load:function(){
				projectChart();
				
				
			},
			
			resize:function(){
				handleWorldMap();
				earningChart();
			}
		}
	
	}();

	
		
	jQuery(window).on('load',function(){
		setTimeout(function(){
			dzChartlist.load();
		}, 1000); 
		
	});

     

})(jQuery);
