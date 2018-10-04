/*
* 库存选择模态框
* appendId: 表格ID
* */
function modal_stock(appendId, url, key) {
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
                $('#stocks').append(
                    '<tr><td>' + data[i].id + '</td>' +
                    '<td>' + data[i].item_name + '</td>' +
                    '<td>' + data[i].item_standard + '</td>' +
                    '<td>' + data[i].item_unit + '</td>' +
                    '<td>' + data[i].item_costprice + '</td>' +
                    '<td>' + data[i].costprice + '</td>' +
                    '<td>' + data[i].store + '</td>' +
                    '<td>' + data[i].qty + '</td>' +
                    '<td>' + data[i].cate + '</td></tr>'
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