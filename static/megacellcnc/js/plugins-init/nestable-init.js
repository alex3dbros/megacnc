(function ($) {
    "use strict"


/*******************
Nestable
*******************/
	
	var e = function (e) {
		var t = e.length ? e : $(e.target)
	};
	$("#nestable").nestable({
			group: 1
		}).on("change", e),
		$("#nestable2").nestable({
			group: 1
		}).on("change", e), e($("#nestable").data("output", $("#nestable-output"))), e($("#nestable2").data("output", $("#nestable2-output"))), $("#nestable-menu").on("click", function (e) {
			var t = $(e.target).data("action");
			"expand-all" === t && $(".dd").nestable("expandAll"), "collapse-all" === t && $(".dd").nestable("collapseAll")
		}), $("#nestable3").nestable();



})(jQuery);