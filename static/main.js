function renderTable(data) {
    const table = $("#editable-table");
    // 清空表格内容
    table.find('tbody').empty();
    let max_id = 0;
    data.forEach(row => {
        if (row.id > max_id) max_id = row.id;
        const tr = $("<tr></tr>").attr("data-id", row.id);
        // 填充表格行的五列
        for (let i = 0; i < 5; i++) {
            const td = $("<td contenteditable='false'></td>").text(row.content);
            tr.append(td);
        }
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
    for (let i = 0; i < 5; i++) {
        const td = $("<td contenteditable='true'></td>").text('');
        tr.append(td);
    }
    const button = $("<button></button>").text("添加");
    button.on("click", function() {
        createRow(tr, button);
    });
    tr.append($("<td></td>").append(button));
    table.append(tr);
}

function getData() {
    $.ajax({
        url: '/get-data',
        method: 'GET',
        success: function (data) {
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
    const rowData = row.find("td").map(function() {
        return $(this).text();
    }).get();

    $.ajax({
        url: '/create-row',
        method: 'POST',
        data: {
            row_id: rowId,
            content: rowData
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
