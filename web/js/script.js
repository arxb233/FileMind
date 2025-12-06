const contextMenu = document.getElementById("context-menu");

const menuItems = [
    { label: "加载思维导图", action: (path) => LoadMind(path) },
    { label: "打开", action: (path) => openPath(path) },
];

function showContextMenu(x, y, path) {
    contextMenu.innerHTML = "";
    menuItems.forEach(item => {
        const div = document.createElement("div");
        div.textContent = item.label;
        div.onclick = () => { item.action(path); hideContextMenu(); };
        contextMenu.appendChild(div);
    });
    contextMenu.style.left = x + "px";
    contextMenu.style.top = y + "px";
    contextMenu.style.display = "block";
}

function hideContextMenu() {
    contextMenu.style.display = "none";
}

document.addEventListener("click", hideContextMenu);

async function loadTree(path = null) {
    const url = path ? `/api/tree?path=${encodeURIComponent(path)}` : "/api/tree";
    const res = await fetch(url);
    const data = await res.json();

    const container = document.getElementById("markmap-tree-md");
    if (!container) return;

    // 直接覆盖整个容器内容，autoloader 会自动重新渲染
    container.innerHTML = `
                <script type="text/template">
                    ${data.markdown.replace(/<\/script>/gi, "</scr\\ipt>")} <!-- 防止脚本注入 -->
                <\/script>
            `;

    // autoloader 已经监听 DOM 变化，大多数情况下不需要手动调用
    // 但保险起见可以手动触发一次
    window.markmap?.autoLoader?.renderAll?.();
}
// 加载目录统计
async function loadInfo(path = null) {
    const url = path ? `/api/info?path=${encodeURIComponent(path)}` : "/api/info";
    const res = await fetch(url);
    const info = await res.json();
    document.getElementById("info-text").textContent =
        `路径: ${info.path} | 文件夹: ${info.folders} | 文件: ${info.files} | 生成时间: ${info.generated}`;
}

async function loadDrives() {
    const res = await fetch("/api/drives");
    const drives = await res.json();

    const treeData = drives.map(drive => ({
        id: drive,
        text: drive,
        children: true
    }));

    $('#file-tree').jstree({
        'core': {
            'data': function (node, cb) {
                if (node.id === "#") {
                    cb(treeData);
                } else {
                    fetch(`/api/list?path=${encodeURIComponent(node.id)}`)
                        .then(r => r.json())
                        .then(data => {
                            const children = [];

                            data.folders.forEach(f => {
                                const folderPath = node.id.endsWith("\\") ? node.id + f : node.id + "\\" + f;
                                children.push({ id: folderPath, text: f, children: true });
                            });

                            data.files.forEach(f => {
                                const filePath = node.id.endsWith("\\") ? node.id + f : node.id + "\\" + f;
                                children.push({ id: filePath, text: f, children: false, icon: "jstree-file" });
                            });

                            cb(children);
                        })
                        .catch(err => { console.error("加载子节点失败:", err); cb([]); });
                }
            },
            'check_callback': true,
            'themes': { 'dots': true, 'icons': true }
        }
    });

    // jsTree 右键菜单绑定
    $('#file-tree').on("contextmenu", ".jstree-anchor", function (e) {
        e.preventDefault();
        const node = $.jstree.reference(this).get_node(this);
        showContextMenu(e.pageX, e.pageY, node.id);
    });
}

// 点击文件/文件夹打开
function openPath(path) {
    fetch('/api/open', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path })
    });
}
function LoadMind(path) {
    loadTree(path);
    loadInfo(path);
}

document.addEventListener('click', (e) => {
    const target = e.target;
    const { path, type } = target.dataset || {};

    if (target.tagName === 'A' && path) {
        e.preventDefault();
        fetch('/api/open', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, type })
        });
    }
});

async function init() {
    await loadDrives();
    await loadTree();
}

init();