// 连接WebSocket
var protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
var namespace = '/table';
var socket = io.connect(protocol + window.location.hostname + ':' + location.port + namespace);

// 监听cell_update事件
socket.on('status_change', function (data) {
    // 根据接收到的数据更新表格
    console.log('status change', data);
    change_status(data);
});


socket.on('server_response', function (data) {
    // 根据接收到的数据更新表格
    console.log('server response', data);
});


function set_status_td(td, row) {
    td.text(row.status);
    let backgroundColor;
    switch (row.status) {
        case 'identical':
            backgroundColor = '#00BFFF';   // DeepSkyBlue
            break; 
        case 'done':
            backgroundColor = '#7CFC00';    // LawnGreen
            break;
        case 'error':
            backgroundColor = '#DC143C';    // Crimson
            break;
        default:
            backgroundColor = '#FFD700';    // Gold
            break;
    }

    td.css('background-color', backgroundColor);
    td.on('mouseover', () => {
        // Display the detailed information on mouseover
        // For example, you can use the native `title` attribute, or create a custom tooltip
        td.attr('title', `创建时间：${row.create_time}\n更新时间：${row.update_time}`);
    });
}


function change_status(row) {
    // 选择具有data-id为5的tr元素
    var tr = $(`tr[data-id="${row.id}"]`);
    // 选择tr下的第六个td元素，即status（注意：eq()方法的索引从0开始）
    var td = tr.find('td:eq(5)');
    // 将第六个td元素的内容更改为"done"
    // td.text(row.status);
    set_status_td(td, row);

    tr.find('td:eq(4)').text(row.target);
    tr.find('td:eq(6)').text(row.size);
}

function get_selection_td(value='single time', disabled=false) {
    const options = ["daily", "weekly", "monthly", "single time"];
    const select = $("<select></select>");

    options.forEach((optionValue) => {
        const option = $("<option></option>").text(optionValue).val(optionValue);
        if (optionValue === value) option.attr("selected", "selected");
        select.append(option);
    });
    select.prop("disabled", disabled);

    return td = $(`<td></td>`).append(select);
}

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
        tr.append(get_selection_td(row.frequency, true))
        add_contend(row.user);
        add_contend(row.department);
        add_contend(row.target);
        let td = $("<td contenteditable='false'></td>").text(row.status);
        set_status_td(td, row);
        tr.append(td);
        add_contend(row.size);

        // 添加“编辑/提交”按钮
        let operation = $("<td></td>");
        let button = $("<button></button>").text("编辑");
        button.on("click", function () {
            toggleEditMode(tr, button);
        });
        operation.append(button);

        let button2 = $("<button></button>").text("删除");
        button2.on("click", function () {
            deleteRow(tr);
        });
        operation.append(button2);

        let button3 = $("<button></button>").text("重运行");
        button3.on("click", function () {
            createRow(tr);
        });
        operation.append(button3);

        tr.append(operation);
        table.append(tr);
    });

    // 添加一个空行作为最后一行
    const tr = $("<tr></tr>").attr("data-id", max_id + 1);
    for (let i = 0; i < 7; i++) {
        if (i===1) {
            tr.append(get_selection_td())
        } else{
            const td = $(`<td contenteditable='${i < 4 ? 'true' : 'false'}'></td>`).text('');
            tr.append(td);
        }
    }
    const button = $("<button></button>").text("运行");
    button.on("click", function () {
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

function getRowData(row) {
    let rowData = [];
    $(row).find('td').each(function () {
        // 提取文本内容并添加到数组中
        rowData.push($(this).text());
    });
    rowData[1] = row.find("td:eq(1)").find("select").val();

    console.log(rowData);
    return JSON.stringify(rowData.slice(0, rowData.length - 1));
}

function toggleEditMode(row, button) {
    const isEditable = row.find("td[contenteditable='true']").length > 0;
    // 切换表格行的编辑状态
    row.find("td:lt(4)").attr("contenteditable", !isEditable);
    let select = row.find("td:eq(1)").find("select");
    let isEnabled = !select.prop("disabled");
    select.prop("disabled", isEnabled);

    // 更改按钮文本
    button.text(isEditable ? "编辑" : "提交");

    if (isEditable) {
        // 提交表格行数据到后端
        const rowId = row.attr("data-id");
        const rowData = getRowData(row);

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
                    change_status(response.row);
                } else {
                    console.log("Error updating cell");
                }
            }
        });
    }
}

function createRow(row) {
    // 你需要在后端实现一个新的路由以处理这个请求
    const rowData = getRowData(row);

    $.ajax({
        url: '/create-row',
        method: 'POST',
        data: {
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

function deleteRow(row) {
    const rowId = row.attr("data-id");
    var r = confirm(`是否确定删除id=${rowId}行？`);
    if (r == false) {
        console.log("你按下了\"取消\"按钮!");
        return;
    }
    $.ajax({
        url: '/delete-row',
        method: 'POST',
        data: {
            row_id: rowId
        },
        success: function (response) {
            if (response.status === 'success') {
                console.log("New row deleted successfully");
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
