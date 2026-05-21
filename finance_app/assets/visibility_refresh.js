window.dash_clientside = Object.assign({}, window.dash_clientside || {}, {
    visibility: {
        reloadOnButtonClick: function (nClicks) {
            if (nClicks) {
                window.location.reload();
            }
            return "";
        },
    },
});
