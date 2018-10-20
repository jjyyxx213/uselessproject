/*
* 用户选择模态框
* appendId: 表格ID
* */
function modal_customer(appendId, url, key) {
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
                $('#customers').append(
                    '<tr><td>' + data[i].id + '</td>' +
                    '<td>' + data[i].name + '</td>' +
                    '<td>' + data[i].phone + '</td>' +
                    '<td>' + data[i].pnumber + '</td>' +
                    '<td>' + data[i].brand + '</td>' +
                    '<td>' + data[i].email + '</td>' +
                    '<td>' + data[i].vip_name + '</td>' +
                    '<td>' + data[i].freq + '</td>' +
                    '<td>' + data[i].summary + '</td>' +
                    '<td class="hide">' + data[i].vip_id + '</td>' +
                    '<td class="hide">' + data[i].balance + '</td>' +
                    '<td class="hide">' + data[i].score + '</td></tr>'
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