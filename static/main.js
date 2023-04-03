// 连接WebSocket
var protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
var namespace = '/table';
var socket = io.connect(protocol + window.location.hostname + ':' + location.port + namespace);

// 监听cell_update事件
socket.on('status_change', function(data) {
  // 根据接收到的数据更新表格
  console.log('status change', data);
  // 选择具有data-id为5的tr元素
  var trElement = $(`tr[data-id="${data.row_id}"]`);
  // 选择tr下的第六个td元素，即status（注意：eq()方法的索引从0开始）
  var tdElement = trElement.find('td:eq(5)');
  // 将第六个td元素的内容更改为"done"
  tdElement.text(data.status);
});

function renderTable(data) {
    const table = $("#editable-table");
    // 清空表格内容
    table.find('tbody').empty();
    let max_id = 0;
    data.forEach(row => {
        if (row.id > max_id) max_id = row.id;
        const tr = $("<tr></tr>").attr("data-id", row.id);
        // 填充表格行的五列
        function add_contend(content) {
            const td = $("<td contenteditable='false'></td>").text(content);
            tr.append(td);
        }
        add_contend(row.source);
        add_contend(row.frequency);
        add_contend(row.user);
        add_contend(row.department);
        add_contend(row.target);
        add_contend(row.status);

        // 添加“编辑/提交”按钮
        const button = $("<button></button>").text("编辑");
        button.on("click", function() {
            toggleEditMode(tr, button);
        });
        tr.append($("<td></td>").append(button));
        table.append(tr);
    });

    // 添加一个空行作为最后一行
    const tr = $("<tr></tr>").attr("data-id", max_id+1);
    for (let i = 0; i < 6; i++) {
        const td = $("<td contenteditable='true'></td>").text('');
        tr.append(td);
    }
    const button = $("<button></button>").text("添加");
    button.on("click", function() {
        createRow(tr);
    });
    tr.append($("<td></td>").append(button));
    table.append(tr);
}

function getData() {
    $.ajax({
        url: '/get-data',
        method: 'GET',
        success: function (data) {
            console.log(data)
            renderTable(data);
        }
    });
}

function toggleEditMode(row, button) {
    const isEditable = row.find("td[contenteditable='true']").length > 0;
    // 切换表格行的编辑状态
    row.find("td").attr("contenteditable", !isEditable);
    // 更改按钮文本
    button.text(isEditable ? "编辑" : "提交");

    if (isEditable) {
        // 提交表格行数据到后端
        const rowId = row.attr("data-id");
        const rowData = row.find("td").map(function() {
            return $(this).text();
        }).get();

        // 在这里添加 AJAX 请求以将数据发送到后端
        $.ajax({
            url: '/update-row',
            method: 'POST',
            data: {
                row_id: rowId,
                content: rowData
            },
            success: function (response) {
                if (response.status === 'success') {
                    console.log("Cell updated successfully");
                } else {
                    console.log("Error updating cell");
                }
            }
        });
    }
}

function createRow(row) {
    // 你需要在后端实现一个新的路由以处理这个请求
    const rowId = row.attr("data-id");
    // const rowData = row.find("td").map(function() {
    //     return $(this).text();
    // }).get();
    let rowData = [];
    $(row).find('td').each(function() {
        // 提取文本内容并添加到数组中
        rowData.push($(this).text());
      });

    console.log(rowId)
    console.log(rowData)

    $.ajax({
        url: '/create-row',
        method: 'POST',
        data: {
            row_id: rowId,
            content: JSON.stringify(rowData.slice(0, rowData.length-1)) 
        },
        success: function (response) {
            if (response.status === 'success') {
                console.log("New row created successfully");
                getData(); // 刷新表格以显示新创建的行
            } else {
                console.log("Error creating new row");
            }
        }
    });
}

$(document).ready(function () {
    getData();
});
