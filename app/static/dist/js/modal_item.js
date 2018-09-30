/*
* 产品选择模态框
* appendId: 表格ID
* */
function modal_item(appendId, url, key) {
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
                            $('#items').append(
                                    '<tr><td>' + data[i].id + '</td>' +
                                    '<td>' + data[i].name + '</td>' +
                                    '<td>' + data[i].qty + '</td>' +
                                    '<td>' + data[i].standard + '</td>' +
                                    '<td>' + data[i].unit + '</td>' +
                                    '<td>' + data[i].costprice + '</td>' +
                                    '<td>' + data[i].salesprice + '</td>' +
                                    '<td>' + data[i].cate + '</td></tr>'
                            );
                            //var option = {"id": data[i][value], "text": data[i][name]};
                            //cbData.push(option);
                        }
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        if (errorThrown != 'abort') {
                            alert('失败了，您操作的太频繁');
                        }
                    }
                })
}