#Static Folder Name
folder_name = "megacellcnc"

dz_array = {
        "public":{
            "favicon":f"{folder_name}/images/favicon.png",
            "description":"Megacell Charger Command & Control",
            "og_title":"Megacell Charger Command & Control",
            "og_description":"Megacell Charger Command & Control Admin",
            "og_image":f"static/{folder_name}/deepcyclepower_logo.jpg",
            "title":"Megacell Charger Command & Control",
        },
        "global":{
            "css":[
                    f"{folder_name}/vendor/bootstrap-select/dist/css/bootstrap-select.min.css",
                    f"{folder_name}/css/style.css",
					f"{folder_name}/css/fa-all.min.css",
					f"{folder_name}/vendor/toastr/css/toastr.min.css",
                ],

            "js":{
                "top":[
                    f"{folder_name}/vendor/global/global.min.js",
                    f"{folder_name}/vendor/bootstrap-select/dist/js/bootstrap-select.min.js",
					f"{folder_name}/vendor/toastr/js/toastr.min.js",
					f"{folder_name}/js/plugins-init/toastr-init.js",
					f"{folder_name}/js/highlight.min.js",
                ],
                "bottom":[
                    f"{folder_name}/js/custom.min.js",
                    f"{folder_name}/js/deznav-init.js",
                ]
            },

        },
        "pagelevel":{
            "megacellcnc":{#AppName
                "megacellcnc_views":{
                    "css":{
						"index": [
							f"{folder_name}/vendor/chartist/css/chartist.min.css",
							f"{folder_name}/vendor/jvmap/jquery-jvectormap.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",

						],
						"settings": [
							f"{folder_name}/vendor/jquery-smartwizard/dist/css/smart_wizard.min.css",
						],
						"employee": [
							f"{folder_name}/vendor/swiper/css/swiper-bundle.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"core_hr": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/clockpicker/css/bootstrap-clockpicker.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"finance": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"task": [
							f"{folder_name}/vendor/swiper/css/swiper-bundle.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"task_summary": [
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"performance": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"project": [
							f"{folder_name}/vendor/tagify/dist/tagify.css",

						],

						"devices": [
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"device_slots": [
							f"{folder_name}/vendor/tagify/dist/tagify.css",
							f"{folder_name}/vendor/swiper/css/swiper-bundle.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
						],

						"project_details": [
							f"{folder_name}/vendor/tagify/dist/tagify.css",
							f"{folder_name}/vendor/swiper/css/swiper-bundle.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
						],

						"reports": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"manage_clients": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"blog_1": [
						],
						"svg_icon": [
						],
						"chat": [
						],
						"user": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"user_roles": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"auto_write": [
						],
						"chatbot": [
							f"{folder_name}/vendor/nouislider/nouislider.min.css",
							f"{folder_name}/vendor/clockpicker/css/bootstrap-clockpicker.min.css",
							f"{folder_name}/vendor/jquery-asColorPicker/css/asColorPicker.min.css",
							f"{folder_name}/vendor/bootstrap-material-datetimepicker/css/bootstrap-material-datetimepicker.css",
						],
						"fine_tune_models": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"import": [
							f"{folder_name}/vendor/dropzone/dist/dropzone.css",
						],
						"prompt": [
							f"{folder_name}/vendor/nouislider/nouislider.min.css",
						],
						"repurpose": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"rss": [
							
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							
						],
						"scheduled": [
							f"{folder_name}/vendor/swiper/css/swiper-bundle.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"setting": [
							
							f"{folder_name}/vendor/nouislider/nouislider.min.css",
							f"{folder_name}/vendor/clockpicker/css/bootstrap-clockpicker.min.css",
							f"{folder_name}/vendor/jquery-asColorPicker/css/asColorPicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
							f"{folder_name}/vendor/bootstrap-material-datetimepicker/css/bootstrap-material-datetimepicker.css",
						],
						"content": [
							f"{folder_name}/vendor/bootstrap-datepicker-master/css/bootstrap-datepicker.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"add_content": [
							f"{folder_name}/vendor/select2/css/select2.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"menu": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/nestable2/css/jquery.nestable.min.css",
						],
						"email_template": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"add_email": [
							f"{folder_name}/vendor/bootstrap-datepicker-master/css/bootstrap-datepicker.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"blog": [
							f"{folder_name}/vendor/bootstrap-datepicker-master/css/bootstrap-datepicker.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"add_blog": [
							f"{folder_name}/vendor/select2/css/select2.min.css",
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"blog_category": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"app_profile_1": [
							f"{folder_name}/vendor/lightgallery/css/lightgallery.min.css",
						],
						"app_profile_2": [
							f"{folder_name}/vendor/lightgallery/css/lightgallery.min.css",
						],
						"edit_profile": [
						],
						"post_details": [
							f"{folder_name}/vendor/lightgallery/css/lightgallery.min.css",
						],
						"customer": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],
						"customer_profile": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],					
						"contacts": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
							
							f"{folder_name}/vendor/bootstrap-datetimepicker/css/bootstrap-datetimepicker.min.css",
							f"{folder_name}/vendor/tagify/dist/tagify.css",
						],					
						"email_compose": [
							f"{folder_name}/vendor/dropzone/dist/dropzone.css",
						],					
						"email_inbox": [
						],					
						"email_read": [
						],					
						"app_calendar": [
							f"{folder_name}/vendor/fullcalendar/css/main.min.css",
						],
						"chart_chartist": [
							f"{folder_name}/vendor/chartist/css/chartist.min.css",
						],
						"chart_chartjs": [
						],
						"chart_flot": [
						],
						"chart_morris": [
						],
						"chart_peity": [
						],
						"chart_sparkline": [
						],
						"ecom_checkout": [
						],
						"ecom_customers": [
						],
						"ecom_invoice": [
						],
						"ecom_product_detail": [
							f"{folder_name}/vendor/star-rating/star-rating-svg.css",
						],
						"ecom_product_grid": [
							f"{folder_name}/vendor/star-rating/star-rating-svg.css",
						],
						"ecom_product_list": [
							f"{folder_name}/vendor/star-rating/star-rating-svg.css",
						],
						"ecom_product_order": [
						],
						"form_editor": [
						],
						"form_element": [
						],
						"form_pickers": [
							f"{folder_name}/vendor/bootstrap-daterangepicker/daterangepicker.css",
							f"{folder_name}/vendor/clockpicker/css/bootstrap-clockpicker.min.css",
							f"{folder_name}/vendor/jquery-asColorPicker/css/asColorPicker.min.css",
							f"{folder_name}/vendor/bootstrap-material-datetimepicker/css/bootstrap-material-datetimepicker.css",
							f"{folder_name}/vendor/pickadate/themes/default.css",
							f"{folder_name}/vendor/pickadate/themes/default.date.css",
						],
						"form_validation": [
						],
						"form_wizard": [
							f"{folder_name}/vendor/jquery-smartwizard/dist/css/smart_wizard.min.css",
						],
						"map_jqvmap": [
							f"{folder_name}/vendor/jqvmap/css/jqvmap.min.css",
						],
						"table_bootstrap_basic": [
						],
						"table_datatable_basic": [
							f"{folder_name}/vendor/datatables/css/jquery.dataTables.min.css",
						],
						"uc_lightgallery": [
							f"{folder_name}/vendor/lightgallery/css/lightgallery.min.css",
						],
						"uc_nestable": [
							f"{folder_name}/vendor/nestable2/css/jquery.nestable.min.css",
						],
						"uc_noui_slider": [
							f"{folder_name}/vendor/nouislider/nouislider.min.css",
						],
						"uc_select2": [
							f"{folder_name}/vendor/select2/css/select2.min.css",
						],
						"uc_sweetalert": [
							f"{folder_name}/vendor/sweetalert2/dist/sweetalert2.min.css",
						],
						"uc_toastr": [
							f"{folder_name}/vendor/toastr/css/toastr.min.css",
						],
						"ui_accordion": [
						],
						"ui_alert": [
						],
						"ui_badge": [
						],
						"ui_button": [
						],
						"ui_button_group": [
						],
						"ui_card": [
						],
						"ui_carousel": [
						],
						"ui_dropdown": [
						],
						"ui_grid": [
						],
						"ui_list_group": [
						],
						"ui_media_object": [
						],
						"ui_modal": [
						],
						"ui_pagination": [
						],
						"ui_popover": [
						],
						"ui_progressbar": [
						],
						"ui_tab": [
						],
						"ui_typography": [
						],
						"widget_basic": [
							f"{folder_name}/vendor/chartist/css/chartist.min.css",
						],
						"page_empty": [
						],
						"page_forgot_password": [
						],
                    },
                    "js":{
						"index": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/apexchart/apexchart.js",
							f"{folder_name}/js/dashboard/dashboard-1.js",
							f"{folder_name}/vendor/draggable/draggable.js",
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/moment.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
							f"{folder_name}/vendor/jqvmap/js/jquery.vmap.min.js",
							f"{folder_name}/vendor/jqvmap/js/jquery.vmap.world.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
							f"{folder_name}/vendor/toastr/js/toastr.min.js",
							f"{folder_name}/js/plugins-init/toastr-init.js",
						],
						"employee": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/apexchart/apexchart.js",
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"core_hr": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/clockpicker/js/bootstrap-clockpicker.min.js",
							f"{folder_name}/vendor/apexchart/apexchart.js",	
							f"{folder_name}/js/plugins-init/clock-picker-init.js",
							f"{folder_name}/js/dashboard/core-hr.js",
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/dropzone/dist/dropzone.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/moment.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"finance": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/moment.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"task": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],

						"device_slots": [
							f"{folder_name}/js/qz/qz-tray.js",
							f"{folder_name}/js/qz/jsrsasign-all-min.js",
							f"{folder_name}/js/qz/qprint.js",


							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",

							f"{folder_name}/vendor/flot/jquery.flot.js",
							f"{folder_name}/vendor/flot/jquery.flot.pie.js",
							f"{folder_name}/vendor/flot/jquery.flot.resize.js",
							f"{folder_name}/vendor/flot/jquery.flot.time.js",
							f"{folder_name}/vendor/flot-spline/jquery.flot.spline.min.js",

							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
							f"{folder_name}/js/device-slots.js",




						],

						"project_details": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
							f"{folder_name}/js/project-details.js",
							f"{folder_name}/js/xlsx.full.min.js",
						],

						"database": [
							f"{folder_name}/js/qz/qz-tray.js",
							f"{folder_name}/js/qz/jsrsasign-all-min.js",
							f"{folder_name}/js/qz/qprint.js",


							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
							f"{folder_name}/js/database.js",
							f"{folder_name}/js/xlsx.full.min.js",


							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",

							f"{folder_name}/vendor/flot/jquery.flot.js",
							f"{folder_name}/vendor/flot/jquery.flot.pie.js",
							f"{folder_name}/vendor/flot/jquery.flot.resize.js",
							f"{folder_name}/vendor/flot/jquery.flot.time.js",
							f"{folder_name}/vendor/flot-spline/jquery.flot.spline.min.js",


						],

						"task_summary": [
							f"{folder_name}/vendor/draggable/draggable.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"performance": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/moment.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"project": [
							f"{folder_name}/vendor/tagify/dist/tagify.js",

						],

						"devices": [
							f"{folder_name}/vendor/tagify/dist/tagify.js",
							f"{folder_name}/js/devices-functions.js",
						],
						"settings": [
							f"{folder_name}/vendor/jquery-steps/build/jquery.steps.min.js",
							f"{folder_name}/vendor/jquery-validation/jquery.validate.min.js",
							f"{folder_name}/js/plugins-init/jquery.validate-init.js",
							f"{folder_name}/vendor/jquery-smartwizard/dist/js/jquery.smartWizard.js",

							f"{folder_name}/js/qz/jsrsasign-all-min.js",
							f"{folder_name}/js/qz/qz-tray.js",
							f"{folder_name}/js/qz/qprint.js",




						],

						"reports": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/moment.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"manage_clients": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/jquery-nice-select/js/jquery.nice-select.min.js",
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/moment.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"blog_1": [
						],
						"svg_icon": [
						],
						"chat": [
						],
						"user": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
						],
						"user_roles": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
						],
						"customer": [
							f"{folder_name}/vendor/apexchart/apexchart.js",
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/moment.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"customer_profile": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/moment.js",
							f"{folder_name}/vendor/bootstrap-datetimepicker/js/bootstrap-datetimepicker.min.js",
						],
						"contacts": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"auto_write": [
						],
						"chatbot": [
							f"{folder_name}/vendor/nouislider/nouislider.min.js",
							f"{folder_name}/vendor/wnumb/wNumb.js",
							f"{folder_name}/vendor/jquery-asColor/jquery-asColor.min.js",
							f"{folder_name}/vendor/jquery-asGradient/jquery-asGradient.min.js",
							f"{folder_name}/vendor/jquery-asColorPicker/js/jquery-asColorPicker.min.js",
							f"{folder_name}/js/plugins-init/jquery-asColorPicker.init.js",
						],
						"fine_tune_models": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
						],
						"imports": [
							f"{folder_name}/vendor/dropzone/dist/dropzone.js",
						],
						"prompt": [
							f"{folder_name}/vendor/nouislider/nouislider.min.js",
							f"{folder_name}/vendor/wnumb/wNumb.js",
						],
						"repurpose": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
						],
						"rss": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
						],
						"scheduled": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/apexchart/apexchart.js",
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/vendor/datatables/js/dataTables.buttons.min.js",
							f"{folder_name}/vendor/datatables/js/buttons.html5.min.js",
							f"{folder_name}/vendor/datatables/js/jszip.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"setting": [
							f"{folder_name}/vendor/nouislider/nouislider.min.js",
							f"{folder_name}/vendor/wnumb/wNumb.js",
							f"{folder_name}/vendor/jquery-asColor/jquery-asColor.min.js",
							f"{folder_name}/vendor/jquery-asGradient/jquery-asGradient.min.js",
							f"{folder_name}/vendor/jquery-asColorPicker/js/jquery-asColorPicker.min.js",
							f"{folder_name}/js/plugins-init/jquery-asColorPicker.init.js",
							f"{folder_name}/vendor/tagify/dist/tagify.js",
						],
						"content": [
							f"{folder_name}/vendor/bootstrap-datepicker-master/js/bootstrap-datepicker.min.js",
							f"{folder_name}/js/dashboard/cms.js",
						],
						"add_content": [
							f"{folder_name}/js/dashboard/cms.js",
							f"{folder_name}/vendor/ckeditor/ckeditor.js",
							f"{folder_name}/vendor/select2/js/select2.full.min.js",
							f"{folder_name}/js/plugins-init/select2-init.js",
						],
						"menu": [
							f"{folder_name}/js/dashboard/cms.js",
							f"{folder_name}/vendor/nestable2/js/jquery.nestable.min.js",
							f"{folder_name}/js/plugins-init/nestable-init.js",
						],
						"email_template": [
							f"{folder_name}/js/dashboard/cms.js",
						],
						"add_email": [
							f"{folder_name}/js/dashboard/cms.js",
							f"{folder_name}/vendor/ckeditor/ckeditor.js",
							f"{folder_name}/vendor/select2/js/select2.full.min.js",
							f"{folder_name}/js/plugins-init/select2-init.js",
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
						],
						"blog": [
							f"{folder_name}/vendor/bootstrap-datepicker-master/js/bootstrap-datepicker.min.js",
							f"{folder_name}/js/dashboard/cms.js",
						],
						"add_blog": [
							f"{folder_name}/js/dashboard/cms.js",
							f"{folder_name}/vendor/ckeditor/ckeditor.js",
							f"{folder_name}/vendor/select2/js/select2.full.min.js",
							f"{folder_name}/js/plugins-init/select2-init.js",
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
						],
						"blog_category": [
							f"{folder_name}/js/dashboard/cms.js",
						],
						"app_calendar": [
							f"{folder_name}/vendor/moment/moment.min.js",
							f"{folder_name}/vendor/fullcalendar/js/main.min.js",
							f"{folder_name}/js/plugins-init/fullcalendar-init.js",
						],
						"app_profile_1": [
							f"{folder_name}/vendor/lightgallery/js/lightgallery-all.min.js",
						],
						"app_profile_2": [
							f"{folder_name}/vendor/lightgallery/js/lightgallery-all.min.js",
						],
						"edit_profile": [
						],
						"post_details": [
							f"{folder_name}/vendor/lightgallery/js/lightgallery-all.min.js",
							f"{folder_name}/vendor/jquery-nice-select/js/jquery.nice-select.min.js",
						],
						"chart_chartist": [
							f"{folder_name}/vendor/chartist/js/chartist.min.js",
							f"{folder_name}/vendor/chartist-plugin-tooltips/js/chartist-plugin-tooltip.min.js",
							f"{folder_name}/js/plugins-init/chartist-init.js",
						],
						"chart_chartjs": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/js/plugins-init/chartjs-init.js",
						],
						"chart_flot": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/flot/jquery.flot.js",
							f"{folder_name}/vendor/flot/jquery.flot.pie.js",
							f"{folder_name}/vendor/flot/jquery.flot.resize.js",
							f"{folder_name}/vendor/flot-spline/jquery.flot.spline.min.js",
							f"{folder_name}/js/plugins-init/flot-init.js",
						],
						"chart_morris": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/raphael/raphael.min.js",
							f"{folder_name}/vendor/morris/morris.min.js",
							f"{folder_name}/js/plugins-init/morris-init.js",
						],
						"chart_peity": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/peity/jquery.peity.min.js",
							f"{folder_name}/js/plugins-init/piety-init.js",

						],
						"chart_sparkline": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/jquery-sparkline/jquery.sparkline.min.js",
							f"{folder_name}/js/plugins-init/sparkline-init.js",
							f"{folder_name}/vendor/svganimation/vivus.min.js",
							f"{folder_name}/vendor/svganimation/svg.animation.js",
						],
						"ecom_checkout": [
						],
						"ecom_customers": [
									
						],
						"ecom_invoice": [
						],
						"ecom_product_detail": [
							f"{folder_name}/vendor/star-rating/jquery.star-rating-svg.js",
							f"{folder_name}/vendor/owl-carousel/owl.carousel.js",
						],
						"ecom_product_grid": [
						],
						"ecom_product_list": [
							f"{folder_name}/vendor/star-rating/jquery.star-rating-svg.js",
						],
						"ecom_product_order": [
						],
						"email_compose": [
							f"{folder_name}/vendor/jquery-nice-select/js/jquery.nice-select.min.js",
							f"{folder_name}/vendor/dropzone/dist/dropzone.js",
						],
						"email_inbox": [
						],
						"email_read": [
						],
						"form_editor": [
							f"{folder_name}/vendor/ckeditor/ckeditor.js",
						],
						"form_element": [
						],
						"form_pickers": [
							f"{folder_name}/vendor/moment/moment.min.js",
							f"{folder_name}/vendor/bootstrap-daterangepicker/daterangepicker.js",
							f"{folder_name}/vendor/clockpicker/js/bootstrap-clockpicker.min.js",
							f"{folder_name}/vendor/jquery-asColor/jquery-asColor.min.js",
							f"{folder_name}/vendor/jquery-asGradient/jquery-asGradient.min.js",
							f"{folder_name}/vendor/jquery-asColorPicker/js/jquery-asColorPicker.min.js",
							f"{folder_name}/vendor/bootstrap-material-datetimepicker/js/bootstrap-material-datetimepicker.js",
							f"{folder_name}/vendor/pickadate/picker.js",
							f"{folder_name}/vendor/pickadate/picker.time.js",
							f"{folder_name}/vendor/pickadate/picker.date.js",
							f"{folder_name}/js/plugins-init/bs-daterange-picker-init.js",
							f"{folder_name}/js/plugins-init/clock-picker-init.js",
							f"{folder_name}/js/plugins-init/jquery-asColorPicker.init.js",
							f"{folder_name}/js/plugins-init/material-date-picker-init.js",
							f"{folder_name}/js/plugins-init/pickadate-init.js",
						],
						"form_validation_jquery": [
							f"{folder_name}/vendor/jquery-validation/jquery.validate.min.js",
							f"{folder_name}/js/plugins-init/jquery.validate-init.js",
						],
						"form_wizard": [
							f"{folder_name}/vendor/jquery-steps/build/jquery.steps.min.js",
							f"{folder_name}/vendor/jquery-validation/jquery.validate.min.js",
							f"{folder_name}/js/plugins-init/jquery.validate-init.js",
							f"{folder_name}/vendor/jquery-smartwizard/dist/js/jquery.smartWizard.js",
						],
						"map_jqvmap": [
							f"{folder_name}/vendor/jqvmap/js/jquery.vmap.min.js",
							f"{folder_name}/vendor/jqvmap/js/jquery.vmap.world.js",
							f"{folder_name}/vendor/jqvmap/js/jquery.vmap.usa.js",
							f"{folder_name}/js/plugins-init/jqvmap-init.js",
						],
						
						"page_error_400": [
						],
						"page_error_403": [
						],
						"page_error_404": [
						],
						"page_error_500": [
						],
						"page_error_503": [
						],
						"page_empty": [
						],
						"page_lock_screen": [
							f"{folder_name}/vendor/deznav/deznav.min.js",
						],
						"page_login": [
						],
						"page_forgot_password": [
						],
						"page_register": [
						],
						"table_bootstrap_basic": [
							f"{folder_name}/js/highlight.min.js",
						],
						"table_datatable_basic": [
							f"{folder_name}/vendor/datatables/js/jquery.dataTables.min.js",
							f"{folder_name}/js/plugins-init/datatables.init.js",
							f"{folder_name}/js/highlight.min.js",
						],
						"uc_lightgallery": [
							f"{folder_name}/vendor/lightgallery/js/lightgallery-all.min.js",
						],
						"uc_nestable": [
							f"{folder_name}/vendor/nestable2/js/jquery.nestable.min.js",
							f"{folder_name}/js/plugins-init/nestable-init.js",
						],
						"uc_noui_slider": [
							f"{folder_name}/vendor/nouislider/nouislider.min.js",
							f"{folder_name}/vendor/wnumb/wNumb.js",
							f"{folder_name}/js/plugins-init/nouislider-init.js",
						],
						"uc_select2": [
							f"{folder_name}/vendor/select2/js/select2.full.min.js",
							f"{folder_name}/js/plugins-init/select2-init.js",
						],
						"uc_sweetalert": [
							f"{folder_name}/vendor/sweetalert2/dist/sweetalert2.min.js",
							f"{folder_name}/js/plugins-init/sweetalert.init.js",
						],
						"uc_toastr": [
							f"{folder_name}/vendor/toastr/js/toastr.min.js",
							f"{folder_name}/js/plugins-init/toastr-init.js",
						],
						"ui_accordion": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_alert": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_badge": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_button": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_button_group": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_card": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_carousel": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_dropdown": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_grid": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_list_group": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_media_object": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_modal": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_pagination": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_popover": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_progressbar": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_tab": [
							f"{folder_name}/js/highlight.min.js",
						],
						"ui_typography": [
							f"{folder_name}/js/highlight.min.js",
						],
						"widget_basic": [
							f"{folder_name}/vendor/chart.js/Chart.bundle.min.js",
							f"{folder_name}/vendor/apexchart/apexchart.js",
							f"{folder_name}/vendor/chartist/js/chartist.min.js",
							f"{folder_name}/vendor/chartist-plugin-tooltips/js/chartist-plugin-tooltip.min.js",
							f"{folder_name}/vendor/flot/jquery.flot.js",
							f"{folder_name}/vendor/flot/jquery.flot.pie.js",
							f"{folder_name}/vendor/flot/jquery.flot.resize.js",
							f"{folder_name}/vendor/flot-spline/jquery.flot.spline.min.js",
							f"{folder_name}/vendor/jquery-sparkline/jquery.sparkline.min.js",
							f"{folder_name}/js/plugins-init/sparkline-init.js",
							f"{folder_name}/vendor/peity/jquery.peity.min.js",
							f"{folder_name}/js/plugins-init/piety-init.js",
							f"{folder_name}/js/plugins-init/widgets-script-init.js",
						],
                    },
                }
            }
        }


}