/*
* 微信二维码模态框
* appendId: 表格ID
* */
function modal_wechat_qrcode(appendId, url, key) {
    $.ajax({
        url: url,
        type: "GET",
        data: "key=" + key,
        dataType: "json",
        success: function (result) {
            appendId.empty();
            appendId.append(result.qrcode);
        },
        error: function (jqXHR, textStatus, errorThrown) {
            if (errorThrown != 'abort') {
                alert('失败了，您操作的太频繁');
            }
        }
    })
}