/**
 * Shared history-chart timeframe (localStorage) for device-slots & database pages.
 * Default: 5m (5-minute buckets) for fast load; denser: 1m, 30s, 10s.
 */
(function (global) {
    var STORAGE_KEY = 'megacnc.historyChartTimeframe';
    var OPTIONS = ['5m', '1m', '30s', '10s'];

    function getSavedHistoryTimeframe() {
        try {
            var v = localStorage.getItem(STORAGE_KEY);
            if (OPTIONS.indexOf(v) !== -1) return v;
        } catch (e) { /* private mode */ }
        return '5m';
    }

    function saveHistoryTimeframe(v) {
        if (OPTIONS.indexOf(v) === -1) return;
        try {
            localStorage.setItem(STORAGE_KEY, v);
        } catch (e) { /* ignore */ }
    }

    function optionTags(selected) {
        var sel = selected || getSavedHistoryTimeframe();
        function opt(val, label) {
            return '<option value="' + val + '"' + (sel === val ? ' selected' : '') + '>' + label + '</option>';
        }
        return (
            opt('5m', '5 min (default, fast)') +
            opt('1m', '1 min') +
            opt('30s', '30 sec') +
            opt('10s', '10 sec (dense)')
        );
    }

    global.MegaCNCChartTimeframe = {
        STORAGE_KEY: STORAGE_KEY,
        OPTIONS: OPTIONS,
        get: getSavedHistoryTimeframe,
        save: saveHistoryTimeframe,
        optionTags: optionTags
    };
})(typeof window !== 'undefined' ? window : this);
