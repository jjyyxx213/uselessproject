/**
 * ajax获取select2下拉框数据（带鼠标滚动分页）
 * @param selectId 下拉框id
 * @param options 选项，包含如下字段：
 * url 数据接口url
 * pageSize 每次加载的数据条数
 * name 下拉框显示字段名称
 * value 下拉框value字段名称
 * placeholder 默认显示的文字
 * selected 默认选中项，格式：[{id:1,text:"选项1"},{id:2,text:"选项2"}]
 * formatResult 返回结果回调函数，可以在该回调中，自定义下拉框数据的显示样式，比如：加入图片等
 * templateSelection 选中项回调，该参数必须与formatResult参数搭配使用
 * 注意点1 : 后端接口需返回 data（具体数据）和 pages（总页数）两个字段
 * 注意点2 : 两个自定义的回调函数中，必须要把处理结果return回来，如果没有传入formatResult参数，则采用默认的显示样式
 */

function ajaxSelect2(selectId, options, formatResult, formatSelected) {
    var value = options["value"];
    var name = options["name"];
    var flag = (typeof formatResult === "function") ? true : false;
    var select2Option = {
        language: "zh-CN",
        allowClear: true,
        placeholder: options["placeholder"] || "请选择",
        ajax: {
            url: options["url"],
            type: "post",
            dataType: "json",
            delay: 250,
            data: function (params) {
                // 传递到后端的参数
                return {
                    // 搜索框内输入的内容
                    selectInput: params.term,
                    // 当前页
                    curPage: params.page || 1,
                    // 每页显示多少条记录，默认10条
                    //pageSize: options["pageSize"] || 3
                };
            },
            cache: true,
            processResults: function (res, params) {
                params.page = params.page || 1;
                var cbData = [];
                if (flag) {
                    cbData = res.data;
                } else {
                    var data = res.data;
                    var len = data.length;
                    for (var i = 0; i < len; i++) {
                        var option = {"id": data[i][value], "text": data[i][name]};
                        cbData.push(option);
                    }
                }
                return {
                    results: cbData,
                    //如果per_page太小（比如3），会无法触发滚动条事件！！！！！！！！！！！！
                    pagination: {
                        more: params.page < res.pages
                    }
                };
            }
        },
        escapeMarkup: function (markup) {
            // 字符转义处理
            return markup;
        },
        // 最少输入N个字符才开始检索，如果想在点击下拉框时加载数据，请设置为 0
        minimumInputLength: 1
    };
    if (flag) {
        select2Option.templateResult = formatResult;
        select2Option.templateSelection = formatSelected;
    }
    var $select = $("#" + selectId);
    $select.select2(select2Option);
    if (!flag) {
        // 默认选中项设置
        var html = '';
        var values = [];
        var selected = options['selected'];
        if (selected) {
            $.each(selected, function (index, item) {
                values.push(item.id);
                html += '<option value="' + item.id + '">' + item.text + '</option>';
            });
            $select.append(html);
            $select.val(values).trigger('change');
        }
    }
}