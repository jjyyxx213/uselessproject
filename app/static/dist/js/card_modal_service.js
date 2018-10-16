/*
* 会员卡服务选择模态框
* appendId: 表格ID
* */
function card_modal_service(appendId, url, key) {
    $.ajax({
        url: url,
        type: "GET",
        data: "key=" + key,
        dataType: "json",
        success: function (result) {
            appendId.empty();
            var data = result.data;
            var len = data.length;
            for (var i = 0; i < len; i++) {
                $('#services').append(
                    '<tr><td>' + data[i].item_id + '</td>' +
                    '<td>' + data[i].item_name + '</td>' +
                    '<td>' + data[i].item_standard + '</td>' +
                    '<td>' + data[i].item_unit + '</td>' +
                    '<td>' + data[i].item_salesprice + '</td>' +
                    '<td>' + data[i].item_cate + '</td></tr>'
                );
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            if (errorThrown != 'abort') {
                alert('失败了，您操作的太频繁');
            }
        }
    })
}