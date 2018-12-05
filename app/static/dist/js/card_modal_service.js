/*
* 会员卡服务选择模态框
* appendId: 表格ID
* */
function card_modal_service(url) {
   $('#services').bootstrapTable({
        url: url, //请求后台的URL（*）
        method: 'GET',                      //请求方式（*）
        toolbar: '#toolbar',                //工具按钮用哪个容器
        striped: true,                      //是否显示行间隔色
        cache: false,                       //是否使用缓存，默认为true，所以一般情况下需要设置一下这个属性（*）
        pagination: true,                   //是否显示分页（*）
        //sortName: "id",                     //排序字段
        sortable: true,                     //是否启用排序
        sortOrder: "desc",                   //排序方式
        sidePagination: "client",           //分页方式：client客户端分页，server服务端分页（*）
        //queryParams: queryParams,//传递参数（*）
        pageNumber: 1,                       //初始化加载第一页，默认第一页
        pageSize: 50,                       //每页的记录行数（*）
        pageList: [10, 25, 50, 100],        //可供选择的每页的行数（*）
        search: true,                       //是否显示表格搜索，此搜索是客户端搜索，不会进服务端，所以，个人感觉意义不大
        strictSearch: false,                //设置为 true启用全匹配搜索，否则为模糊搜索。
        showColumns: true,                  //是否显示所有的列
        showRefresh: true,                  //是否显示刷新按钮
        minimumCountColumns: 2,             //最少允许的列数
        clickToSelect: true,                //是否启用点击选中行
        height: 500,                        //行高，如果没有设置height属性，表格自动根据记录条数觉得表格高度
        uniqueId: "ID",                     //每一行的唯一标识，一般为主键列
        showToggle: false,                    //是否显示详细视图和列表视图的切换按钮
        cardView: false,                    //是否显示详细视图
        detailView: false,                   //是否显示父子表
        columns: [ {
            field: 'item_id',
            title: '编号',
            valign: 'middle',
            sortable: true
        }, {
            field: 'item_name',
            title: '名称',
            valign: 'middle',
            sortable: true
        },  {
            field: 'item_standard',
            title: '规格',
            valign: 'middle',
            sortable: true
        }, {
            field: 'item_unit',
            title: '单位',
            valign: 'middle',
            sortable: true
        },{
            field: 'item_salesprice',
            title: '销售价',
            valign: 'middle',
            sortable: true
        }, {
            field: 'item_cate',
            title: '商品类型',
            valign: 'middle',
            sortable: true
        }, ]
    });
}