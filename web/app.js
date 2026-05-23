const samples = {
  variables: {
    source_name: "04_variables.nc",
    code: `%\nO1004\nN10 #500 = #100 + #101\nN20 #<RESULT> = #500\nN30 IF [#<RESULT> GT 10] GOTO 80\nN40 #102 = 0\nN50 GOTO 90\nN80 #102 = 1\nN85 M98 P2000\nN90 IF [#102 EQ 1] THEN #103 = #<RESULT>\nN100 M30\n%`,
  },
  machineMcode: {
    source_name: "machine_mcode.nc",
    code: `%\nO1005\nN10 #100 = 1\nN20 M123\nN30 IF [#100 EQ 1] GOTO 90\nN40 M30\n%`,
  },
  longJump: {
    source_name: "06_long_jump_connector.nc",
    code: `%\nO1006 (long jump connector sample)\nN10 #100 = 1\nN20 IF [#100 EQ 1] GOTO 90\nN30 #101 = 10\nN40 #102 = #101 + 5\nN50 GOTO 100\nN60 #103 = 0\nN70 M123\nN80 #104 = #102\nN90 M98 P2000\nN100 M30\n%`,
  },
};

const commonMCodes = {
  M0: "プログラム停止",
  M00: "プログラム停止",
  M1: "任意停止",
  M01: "任意停止",
  M2: "プログラム終了",
  M02: "プログラム終了",
  M3: "主軸を正転",
  M03: "主軸を正転",
  M4: "主軸を逆転",
  M04: "主軸を逆転",
  M5: "主軸停止",
  M05: "主軸停止",
  M8: "クーラントON",
  M08: "クーラントON",
  M9: "クーラントOFF",
  M09: "クーラントOFF",
  M30: "プログラム終了",
  M98: "別のプログラムを呼び出す処理",
};

const sampleSelect = document.querySelector("#sample-select");
const sourceCode = document.querySelector("#source-code");
const chooseFileButton = document.querySelector("#choose-file-button");
const fileInput = document.querySelector("#file-input");
const fileName = document.querySelector("#file-name");
const analyzeButton = document.querySelector("#analyze-button");
const saveButton = document.querySelector("#save-button");
let latestAnalysis = null;
let currentSourceName = samples.variables.source_name;

sampleSelect.addEventListener("change", () => {
  sourceCode.value = samples[sampleSelect.value].code;
  currentSourceName = samples[sampleSelect.value].source_name;
  fileName.textContent = "サンプルを表示しています。自分のNCファイルも選べます。";
});

chooseFileButton.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.addEventListener("load", () => {
    sourceCode.value = String(reader.result || "");
    currentSourceName = file.name;
    fileName.textContent = `${file.name} を読み込みました。`;
  });
  reader.addEventListener("error", () => {
    fileName.textContent = "ファイルを読み取れませんでした。もう一度選び直してください。";
  });
  reader.readAsText(file);
});

analyzeButton.addEventListener("click", () => {
  const analysis = analyzeNcMacro(currentSourceName, sourceCode.value);
  renderAnalysis(analysis);
});

saveButton.addEventListener("click", () => {
  latestAnalysis = analyzeNcMacro(currentSourceName, sourceCode.value);
  renderAnalysis(latestAnalysis);
  const blob = new Blob([buildFriendlyReport(latestAnalysis)], { type: "text/markdown;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${latestAnalysis.source_name.replace(/\.[^.]+$/, "") || "nc-result"}-memo.md`;
  link.click();
  URL.revokeObjectURL(link.href);
});

document.querySelectorAll(".view-tab").forEach((button) => {
  button.addEventListener("click", () => {
    activateView(button.dataset.view, true);
  });
});

function activateView(targetId, persist = false) {
  document.querySelectorAll(".view-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.view === targetId);
  });
  document.querySelectorAll(".view-panel").forEach((panel) => {
    const active = panel.id === targetId;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
  });
  if (persist && window.sessionStorage) {
    window.sessionStorage.setItem("ncMacroVisualizer.activeView", targetId);
  }
}

function restoreActiveView() {
  const stored = window.sessionStorage?.getItem("ncMacroVisualizer.activeView");
  const target = document.getElementById(stored || "") ? stored : "pad-output";
  activateView(target, false);
}

function analyzeNcMacro(sourceName, code) {
  const rawLines = code.split(/\r?\n/);
  const programLines = rawLines
    .map((text, index) => ({ line_no: index + 1, text: text.trim() }))
    .filter((line) => line.text && line.text !== "%");

  const variableMap = new Map();
  const variable_dependencies = [];
  const controls = [];
  const m_codes = [];
  const warnings = [];

  programLines.forEach((line) => {
    const variables = line.text.match(/#<[^>]+>|#\d+/g) || [];
    const assignment = line.text.match(/(#<[^>]+>|#\d+)\s*=/);
    const assignmentTarget = assignment ? assignment[1] : null;

    variables.forEach((name) => {
      if (!variableMap.has(name)) {
        variableMap.set(name, {
          name,
          assignments: [],
          references: [],
          count: 0,
        });
      }

      const entry = variableMap.get(name);
      entry.count += 1;
      if (name === assignmentTarget) {
        entry.assignments.push(line.line_no);
      } else {
        entry.references.push(line.line_no);
      }
    });

    if (assignmentTarget) {
      const rhs = line.text.split("=").slice(1).join("=");
      const sources = [...new Set(rhs.match(/#<[^>]+>|#\d+/g) || [])];
      variable_dependencies.push({
        line_no: line.line_no,
        target: assignmentTarget,
        sources,
        text: line.text,
      });
    }

    const ifGoto = line.text.match(/IF\s*(\[[^\]]+\])\s*GOTO\s*(\d+)/i);
    const ifThen = line.text.match(/IF\s*(\[[^\]]+\])\s*THEN\s*(.+)$/i);
    const gotoOnly = line.text.match(/\bGOTO\s*(\d+)/i);

    if (ifGoto) {
      controls.push({
        line_no: line.line_no,
        kind: "IF_GOTO",
        target: `N${ifGoto[2]}`,
        condition: ifGoto[1],
        text: line.text,
      });
    } else if (ifThen) {
      controls.push({
        line_no: line.line_no,
        kind: "IF_THEN",
        target: null,
        condition: ifThen[1],
        text: line.text,
      });
    } else if (gotoOnly) {
      controls.push({
        line_no: line.line_no,
        kind: "GOTO",
        target: `N${gotoOnly[1]}`,
        condition: null,
        text: line.text,
      });
    }

    const mMatches = line.text.match(/\bM\d+\b/gi) || [];
    mMatches.forEach((rawCode) => {
      const codeName = rawCode.toUpperCase();
      const description = commonMCodes[codeName] || "意味の確認が必要なMコード";
      const status = commonMCodes[codeName] ? "一般的な意味あり" : "確認が必要";
      m_codes.push({
        code: codeName,
        line_no: line.line_no,
        status,
        description,
        text: line.text,
      });
      if (!commonMCodes[codeName]) {
        warnings.push({
          kind: "machine_specific_m_code",
          line_no: line.line_no,
          message: `${codeName} は意味の確認が必要なMコードです。機械の説明書、PMC、ビルダー設定を確認してください。`,
        });
      }
    });
  });

  const labelSet = new Set(
    programLines
      .map((line) => line.text.match(/^N\d+/i)?.[0].toUpperCase())
      .filter(Boolean),
  );
  controls.forEach((control) => {
    if ((control.kind === "IF_GOTO" || control.kind === "GOTO") && !labelSet.has(control.target)) {
      warnings.push({
        kind: "unresolved_goto",
        line_no: control.line_no,
        message: `${control.target} という飛び先が見つからないジャンプがあります。元のNCを確認してください。`,
      });
    }
  });

  return {
    source_name: sourceName,
    line_count: rawLines.filter((line) => line.trim()).length,
    variable_summary: [...variableMap.values()].sort((a, b) =>
      a.name.localeCompare(b.name, "en"),
    ),
    controls,
    variable_dependencies,
    m_codes,
    warnings,
    flow: buildFlowGraph(programLines, controls),
  };
}

function buildFlowGraph(programLines, controls) {
  const mainNodes = [
    { id: "START", kind: "start", title: "開始", text: "確認を始めます", detail: "" },
    ...programLines
      .filter((line) => /^N\d+/i.test(line.text))
      .map((line) => {
        const id = line.text.match(/^N\d+/i)[0].toUpperCase();
        const translated = translateNcLine(line.text);
        return {
          id,
          line_no: line.line_no,
          kind: getFlowKind(line.text),
          title: translated.title,
          text: translated.summary,
          detail: translated.detail,
        };
      }),
    { id: "END", kind: "end", title: "終了", text: "確認を終えます", detail: "" },
  ];

  const nodes = [];
  const edges = [];
  const nodeById = new Map(mainNodes.map((node) => [node.id, node]));

  mainNodes.forEach((node, index) => {
    nodes.push({
      ...node,
      x: 210,
      y: 32 + index * 108,
    });
  });

  for (let index = 0; index < mainNodes.length - 1; index += 1) {
    const current = mainNodes[index];
    const next = mainNodes[index + 1];
    const control = controls.find((item) => item.line_no === current.line_no);

    if (!control) {
      edges.push({ from: current.id, to: next.id, label: current.id === "START" ? "" : "次へ", kind: "sequential" });
      continue;
    }

    if (control.kind === "IF_THEN") {
      const thenNode = {
        id: `${current.id}_THEN`,
        kind: "then",
        title: "条件が合うと実行",
        text: translateThenAction(control.text),
        detail: control.text.replace(/^.*\bTHEN\s*/i, "THEN "),
        x: 560,
        y: 32 + index * 108,
      };
      nodes.push(thenNode);
      edges.push({ from: current.id, to: next.id, label: "いいえ", kind: "branch_false" });
      edges.push({ from: current.id, to: thenNode.id, label: "はい", route: "branch", kind: "branch_true" });
      edges.push({ from: thenNode.id, to: next.id, label: "", route: "merge", kind: "sequential" });
      continue;
    }

    if (control.kind === "IF_GOTO" && nodeById.has(control.target)) {
      edges.push({ from: current.id, to: next.id, label: "いいえ", kind: "branch_false" });
      edges.push({ from: current.id, to: control.target, label: "はい", route: "jump", kind: "branch_true" });
      continue;
    }

    if (control.kind === "GOTO" && nodeById.has(control.target)) {
      edges.push({ from: current.id, to: control.target, label: `指定場所へ`, route: "jump", kind: "jump" });
      continue;
    }

    edges.push({ from: current.id, to: next.id, label: "次へ", kind: "sequential" });
  }

  return { nodes, edges: suppressMergeLabels(edges) };
}

function suppressMergeLabels(edges) {
  const incoming = new Map();
  edges.forEach((edge, index) => {
    if (!incoming.has(edge.to)) incoming.set(edge.to, []);
    incoming.get(edge.to).push(index);
  });

  const priority = {
    branch_false: 0,
    branch_true: 1,
    sequential: 2,
  };

  const result = edges.map((edge) => ({ ...edge }));
  incoming.forEach((indexes) => {
    if (indexes.length < 2) return;
    const sorted = [...indexes].sort((a, b) => {
      const priorityA = priority[result[a].kind] ?? 99;
      const priorityB = priority[result[b].kind] ?? 99;
      return priorityA - priorityB;
    });
    sorted.slice(1).forEach((index) => {
      result[index].label = "";
    });
  });
  return result;
}

function getFlowKind(text) {
  if (/\bIF\b/i.test(text)) return "decision";
  if (/\bM98\b|\bG65\b/i.test(text)) return "sub";
  const mCode = text.match(/\bM\d+\b/i)?.[0].toUpperCase();
  if (mCode) {
    if (/\bM30\b/i.test(text)) return "end";
    return commonMCodes[mCode] ? "machine" : "warning";
  }
  return "process";
}

function translateNcLine(text) {
  const assignment = text.match(/(#<[^>]+>|#\d+)\s*=\s*(.+)$/);
  const ifGoto = text.match(/IF\s*(\[[^\]]+\])\s*GOTO\s*(\d+)/i);
  const ifThen = text.match(/IF\s*(\[[^\]]+\])\s*THEN\s*(.+)$/i);
  const gotoOnly = text.match(/\bGOTO\s*(\d+)/i);
  const mCode = text.match(/\bM\d+\b/i)?.[0].toUpperCase();

  if (ifGoto) {
    return {
      title: "条件で分かれる",
      summary: `${translateCondition(ifGoto[1])}なら、別の場所へ進みます`,
      detail: text,
    };
  }

  if (ifThen) {
    return {
      title: "条件で処理する",
      summary: `${translateCondition(ifThen[1])}なら、値を入れます`,
      detail: text,
    };
  }

  if (gotoOnly) {
    return {
      title: "指定場所へ進む",
      summary: `次は N${gotoOnly[1]} の処理へ進みます`,
      detail: text,
    };
  }

  if (mCode === "M98" || /\bG65\b/i.test(text)) {
    return {
      title: "別プログラムを呼ぶ",
      summary: "別のプログラムを呼び出す処理です",
      detail: text,
    };
  }

  if (mCode) {
    return {
      title: mCode === "M30" ? "プログラムを終了する" : "機械を動かす",
      summary: commonMCodes[mCode] || "意味の確認が必要なMコードです",
      detail: text,
    };
  }

  if (assignment) {
    const target = assignment[1];
    const sources = [...new Set(assignment[2].match(/#<[^>]+>|#\d+/g) || [])];
    return {
      title: "値を計算する",
      summary: sources.length ? `${sources.join(" と ")} から ${target} を作ります` : `${target} に値を入れます`,
      detail: text,
    };
  }

  return {
    title: "処理する",
    summary: "NCの処理を行います",
    detail: text,
  };
}

function translateThenAction(text) {
  const thenText = text.replace(/^.*\bTHEN\s*/i, "");
  const assignment = thenText.match(/(#<[^>]+>|#\d+)\s*=\s*(.+)$/);
  if (!assignment) return "条件が合うと、この処理を実行します";
  const sources = [...new Set(assignment[2].match(/#<[^>]+>|#\d+/g) || [])];
  return sources.length
    ? `${sources.join(" と ")} から ${assignment[1]} を作ります`
    : `${assignment[1]} に値を入れます`;
}

function translateCondition(condition) {
  return condition
    .replace(/^\[|\]$/g, "")
    .replace(/\bGT\b/gi, "が次より大きい:")
    .replace(/\bLT\b/gi, "が次より小さい:")
    .replace(/\bEQ\b/gi, "が次と同じ:")
    .replace(/\bGE\b/gi, "が次以上:")
    .replace(/\bLE\b/gi, "が次以下:")
    .replace(/\bNE\b/gi, "が次と違う:")
    .replace(/\s+/g, " ")
    .trim();
}

function renderAnalysis(analysis) {
  latestAnalysis = analysis;
  document.querySelector("#line-count").textContent = analysis.line_count;
  document.querySelector("#variable-count").textContent = analysis.variable_summary.length;
  document.querySelector("#mcode-count").textContent = analysis.m_codes.length;
  document.querySelector("#warning-count").textContent = analysis.warnings.length;

  renderFlow(analysis.flow);
  renderNassiShneiderman(analysis.flow);
  renderStructuredTextView(analysis.flow, analysis.source_name);
  renderControls(analysis.controls);
  renderVariables(analysis.variable_summary);
  renderMCodes(analysis.m_codes);
  renderWarnings(analysis.warnings);
  renderReport(analysis);
}

function renderNassiShneiderman(flow) {
  const container = document.querySelector("#pad-output");
  const root = document.createElement("div");
  root.className = "ns-stack";
  const structured = structurizeFlow(flow);
  root.replaceChildren(...structured.map((block) => renderStructuredBlock(block)));
  container.replaceChildren(root);
}

function structurizeFlow(flow) {
  const skip = new Set();
  const nodeById = new Map(flow.nodes.map((node) => [node.id, node]));
  const blocks = [];

  flow.nodes
    .filter((node) => !["START", "END"].includes(node.id))
    .forEach((node) => {
      if (skip.has(node.id)) return;

      if (node.kind === "decision") {
        const trueEdge = flow.edges.find((edge) => edge.from === node.id && edge.kind === "branch_true");
        const trueNode = trueEdge ? nodeById.get(trueEdge.to) : null;
        const children = [];
        if (trueNode && trueNode.id.endsWith("_THEN")) {
          children.push(nodeToBlock(trueNode));
          skip.add(trueNode.id);
        }
        blocks.push({
          ...nodeToBlock(node),
          kind: "if",
          children,
        });
        return;
      }

      blocks.push(nodeToBlock(node));
    });

  return blocks;
}

function nodeToBlock(node) {
  return {
    kind: node.kind === "needs_confirmation" ? "warning" : node.kind === "machine" ? "machine" : node.kind,
    title: node.title,
    text: node.text,
    detail: node.detail,
    children: [],
  };
}

function renderStructuredBlock(block) {
  const element = document.createElement("section");
  element.className = `ns-block ns-${block.kind}`;

  const title = document.createElement("div");
  title.className = "ns-title";
  title.textContent = block.title;
  element.appendChild(title);

  const text = document.createElement("div");
  text.className = "ns-summary";
  text.textContent = block.text;
  element.appendChild(text);

  if (block.detail) {
    const detail = document.createElement("div");
    detail.className = "ns-source";
    detail.textContent = block.detail;
    element.appendChild(detail);
  }

  if (block.kind === "if") {
    const branches = document.createElement("div");
    branches.className = "ns-branches";

    const yes = document.createElement("div");
    yes.className = "ns-branch";
    yes.appendChild(branchLabel("はい"));
    if (block.children.length) {
      block.children.forEach((child) => yes.appendChild(renderStructuredBlock(child)));
    } else {
      yes.appendChild(emptyBlock("別の場所へ進みます"));
    }

    const no = document.createElement("div");
    no.className = "ns-branch";
    no.appendChild(branchLabel("いいえ"));
    no.appendChild(emptyBlock("そのまま次へ"));

    branches.appendChild(yes);
    branches.appendChild(no);
    element.appendChild(branches);
  }

  return element;
}

function branchLabel(text) {
  const label = document.createElement("div");
  label.className = "ns-branch-label";
  label.textContent = text;
  return label;
}

function emptyBlock(text) {
  const empty = document.createElement("div");
  empty.className = "ns-empty";
  empty.textContent = text;
  return empty;
}

function renderStructuredTextView(flow, sourceName) {
  const lines = [`# Structured View: ${sourceName}`, ""];
  structurizeFlow(flow).forEach((block) => {
    appendStructuredText(lines, block, 0);
  });
  document.querySelector("#text-output").textContent = lines.join("\n");
}

function appendStructuredText(lines, block, depth) {
  const prefix = "  ".repeat(depth);
  lines.push(`${prefix}- ${block.title}`);
  if (block.text && block.text !== block.title) lines.push(`${prefix}  ${block.text}`);
  if (block.detail) lines.push(`${prefix}  code: ${block.detail}`);
  if (block.kind === "if") {
    lines.push(`${prefix}  はい:`);
    if (block.children.length) {
      block.children.forEach((child) => appendStructuredText(lines, child, depth + 2));
    } else {
      lines.push(`${prefix}    別の場所へ進みます`);
    }
    lines.push(`${prefix}  いいえ: そのまま次へ`);
  }
}

function renderControls(controls) {
  const body = document.querySelector("#controls-output");
  if (controls.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="4">条件分岐はありません。</td>';
    body.replaceChildren(row);
    return;
  }

  body.replaceChildren(
    ...controls.map((control) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${control.line_no}</td>
        <td>${escapeHtml(toFriendlyControlKind(control.kind))}</td>
        <td>${escapeHtml(control.condition || "-")}</td>
        <td>${escapeHtml(control.target || "-")}</td>
      `;
      return row;
    }),
  );
}

function toFriendlyControlKind(kind) {
  if (kind === "IF_GOTO") return "条件でジャンプ";
  if (kind === "IF_THEN") return "条件で処理";
  if (kind === "GOTO") return "ジャンプ";
  return kind;
}

function renderFlow(flow) {
  const container = document.querySelector("#flow-output");
  const chartHeight = Math.max(...flow.nodes.map((node) => node.y + getNodeHeight(node))) + 40;
  const svg = createSvgElement("svg", {
    class: "flow-chart",
    role: "img",
    "aria-label": "NC macro flowchart",
    viewBox: `0 0 780 ${chartHeight}`,
  });
  const defs = createSvgElement("defs");
  const marker = createSvgElement("marker", {
    id: "arrowhead",
    markerWidth: "10",
    markerHeight: "10",
    refX: "8",
    refY: "3",
    orient: "auto",
    markerUnits: "strokeWidth",
  });
  marker.appendChild(createSvgElement("path", { d: "M0,0 L0,6 L9,3 z", class: "flow-arrow-head" }));
  defs.appendChild(marker);
  svg.appendChild(defs);

  const nodeById = new Map(flow.nodes.map((node) => [node.id, node]));
  const edgeLayer = createSvgElement("g", { class: "flow-edges" });
  const labelLayer = createSvgElement("g", { class: "flow-edge-labels" });
  flow.edges.forEach((edge) => {
    const from = nodeById.get(edge.from);
    const to = nodeById.get(edge.to);
    if (!from || !to) return;
    const rendered = renderEdge(from, to, edge);
    edgeLayer.appendChild(rendered.path);
    if (rendered.label) {
      labelLayer.appendChild(rendered.label);
    }
  });
  svg.appendChild(edgeLayer);

  const nodeLayer = createSvgElement("g", { class: "flow-nodes" });
  flow.nodes.forEach((node) => {
    nodeLayer.appendChild(renderFlowNode(node));
  });
  svg.appendChild(nodeLayer);
  svg.appendChild(labelLayer);
  container.replaceChildren(svg);
}

function renderEdge(from, to, edge) {
  const label = edge.label;
  const fromBox = getNodeBox(from);
  const toBox = getNodeBox(to);
  const isJump = edge.route === "jump";
  const isBranch = edge.route === "branch";
  const isMerge = edge.route === "merge";
  const laneX = 725;
  let path;
  let labelX;
  let labelY;

  if (isJump) {
    const startX = fromBox.right + 8;
    const startY = fromBox.centerY;
    const endX = toBox.right + 8;
    const endY = toBox.centerY;
    path = `M ${startX} ${startY} C ${laneX} ${startY}, ${laneX} ${endY}, ${endX} ${endY}`;
    labelX = laneX - 112;
    labelY = (startY + endY) / 2 - 8;
  } else if (isBranch) {
    const startX = fromBox.right + 6;
    const startY = fromBox.centerY;
    const endX = toBox.left - 6;
    const endY = toBox.centerY;
    path = `M ${startX} ${startY} C ${startX + 56} ${startY}, ${endX - 56} ${endY}, ${endX} ${endY}`;
    labelX = (startX + endX) / 2 - 34;
    labelY = startY - 10;
  } else if (isMerge) {
    const startX = fromBox.centerX;
    const startY = fromBox.bottom + 6;
    const midY = toBox.top - 20;
    const endX = toBox.centerX;
    const endY = toBox.top - 6;
    path = `M ${startX} ${startY} L ${startX} ${midY} L ${endX + 54} ${midY} L ${endX + 54} ${endY} L ${endX} ${endY}`;
    labelX = startX + 18;
    labelY = midY - 6;
  } else if (Math.abs(from.x - to.x) > 40) {
    const startX = fromBox.centerX;
    const startY = fromBox.bottom + 6;
    const endX = toBox.centerX;
    const endY = toBox.top - 6;
    path = `M ${startX} ${startY} C ${startX} ${startY + 28}, ${endX} ${endY - 28}, ${endX} ${endY}`;
    labelX = (startX + endX) / 2 + 12;
    labelY = (startY + endY) / 2 - 8;
  } else {
    const startX = fromBox.centerX;
    const startY = fromBox.bottom + 6;
    const endX = toBox.centerX;
    const endY = toBox.top - 6;
    path = `M ${startX} ${startY} L ${endX} ${endY}`;
    labelX = startX + 12;
    labelY = (startY + endY) / 2 - 6;
  }

  const pathElement = createSvgElement("path", { d: path, class: "flow-line", "marker-end": "url(#arrowhead)" });
  let labelElement = null;

  if (label) {
    labelElement = createSvgElement("text", {
      x: String(labelX),
      y: String(labelY),
      class: "flow-edge-label",
    });
    labelElement.textContent = label;
  }

  return { path: pathElement, label: labelElement };
}

function renderFlowNode(node) {
  const group = createSvgElement("g", { class: `flow-node-svg ${node.kind}` });
  const width = getNodeWidth(node);
  const height = getNodeHeight(node);
  const x = node.x - width / 2;
  const y = node.y;

  const shape = createFlowShape(node, x, y, width, height);
  group.appendChild(shape);

  const title = createSvgElement("text", {
    x: String(x + width / 2),
    y: String(y + (node.kind === "start" || node.kind === "end" ? height / 2 + 5 : node.kind === "decision" ? 26 : 20)),
    class: "flow-node-title",
  });
  title.textContent = node.title || node.id;
  group.appendChild(title);

  if (node.kind !== "start" && node.kind !== "end") {
    wrapSvgText(group, node.text, x + width / 2, y + (node.kind === "decision" ? 46 : 40), width - 34, "flow-node-text");
    if (node.detail) {
      wrapSvgText(group, node.detail, x + width / 2, y + getNodeHeight(node) - 12, width - 40, "flow-node-detail", 1);
    }
  }
  return group;
}

function getNodeBox(node) {
  const width = getNodeWidth(node);
  const height = getNodeHeight(node);
  return {
    left: node.x - width / 2,
    right: node.x + width / 2,
    top: node.y,
    bottom: node.y + height,
    centerX: node.x,
    centerY: node.y + height / 2,
  };
}

function wrapSvgText(group, text, x, y, maxWidth, className = "flow-node-text", maxLines = 2) {
  const lineLength = Math.max(18, Math.floor(maxWidth / 8));
  const chunks = [];
  for (let index = 0; index < text.length; index += lineLength) {
    chunks.push(text.slice(index, index + lineLength));
  }
  chunks.slice(0, maxLines).forEach((chunk, index) => {
    const line = createSvgElement("text", {
      x: String(x),
      y: String(y + index * 17),
      class: className,
    });
    line.textContent = chunk;
    group.appendChild(line);
  });
}

function createFlowShape(node, x, y, width, height) {
  if (node.kind === "decision") {
    return createSvgElement("polygon", {
      points: `${x + width / 2},${y} ${x + width},${y + height / 2} ${x + width / 2},${y + height} ${x},${y + height / 2}`,
    });
  }

  return createSvgElement("rect", {
    x: String(x),
    y: String(y),
    width: String(width),
    height: String(height),
    rx: node.kind === "start" || node.kind === "end" ? "28" : "6",
    ry: node.kind === "start" || node.kind === "end" ? "28" : "6",
  });
}

function getNodeWidth(node) {
  if (node.kind === "then") return 270;
  if (node.kind === "decision") return 320;
  if (node.kind === "start" || node.kind === "end") return 180;
  return 320;
}

function getNodeHeight(node) {
  if (node.kind === "decision") return 92;
  if (node.kind === "start" || node.kind === "end") return 48;
  return 74;
}

function createSvgElement(name, attributes = {}) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => {
    element.setAttribute(key, value);
  });
  return element;
}

function renderVariables(variables) {
  const body = document.querySelector("#variables-output");
  body.replaceChildren(
    ...variables.map((variable) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code>${escapeHtml(variable.name)}</code></td>
        <td>${formatLines(variable.assignments)}</td>
        <td>${formatLines(variable.references)}</td>
        <td>${variable.count}</td>
      `;
      return row;
    }),
  );
}

function renderMCodes(mCodes) {
  const body = document.querySelector("#mcodes-output");
  body.replaceChildren(
    ...mCodes.map((mCode) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code>${escapeHtml(mCode.code)}</code></td>
        <td>${mCode.line_no}</td>
        <td><span class="tag ${mCode.status === "確認が必要" ? "unknown" : ""}">${escapeHtml(mCode.status)}</span></td>
        <td>${escapeHtml(mCode.description)}</td>
      `;
      return row;
    }),
  );
}

function renderWarnings(warnings) {
  const list = document.querySelector("#warnings-output");
  if (warnings.length === 0) {
    const item = document.createElement("li");
    item.textContent = "大きな注意点は見つかりませんでした。ただし、実機での動作確認は別途必要です。";
    list.replaceChildren(item);
    return;
  }

  list.replaceChildren(
    ...warnings.map((warning) => {
      const item = document.createElement("li");
      item.textContent = warning.line_no
        ? `${warning.line_no}行目: ${warning.message}`
        : warning.message;
      return item;
    }),
  );
}

function renderReport(analysis) {
  document.querySelector("#report-output").textContent = buildFriendlyReport(analysis);
}

function buildFriendlyReport(analysis) {
  const lines = [
    `# NC Macro Visualizer 確認メモ: ${analysis.source_name}`,
    "",
    "## まとめ",
    "",
    `- 行数: ${analysis.line_count}`,
    `- 値: ${analysis.variable_summary.length}`,
    `- 条件やジャンプ: ${analysis.controls.length}`,
    `- 機械動作: ${analysis.m_codes.length}`,
    `- 注意点: ${analysis.warnings.length}`,
    "",
    "> このメモはNCマクロを理解するためのものです。実機動作を保証するものではありません。",
    "",
    "## 値のつながり",
    "",
    "| 行 | 値を入れる先 | 使っている値 | NCコード |",
    "| ---: | --- | --- | --- |",
    ...analysis.variable_dependencies.map(
      (item) =>
        `| ${item.line_no} | \`${item.target}\` | ${item.sources.map((source) => `\`${source}\``).join(", ") || "-"} | \`${item.text}\` |`,
    ),
    "",
    "## 条件分岐とジャンプ",
    "",
    "| 行 | 種類 | 条件 | 飛び先 |",
    "| ---: | --- | --- | --- |",
    ...analysis.controls.map(
      (item) => `| ${item.line_no} | ${toFriendlyControlKind(item.kind)} | ${item.condition || "-"} | ${item.target || "-"} |`,
    ),
    "",
    "## 機械動作",
    "",
    "| 行 | Mコード | 確認 | 説明 |",
    "| ---: | --- | --- | --- |",
    ...analysis.m_codes.map(
      (item) => `| ${item.line_no} | \`${item.code}\` | ${item.status} | ${item.description} |`,
    ),
    "",
    "## 注意点",
    "",
    ...(analysis.warnings.length
      ? analysis.warnings.map((warning) => `- ${warning.line_no ? `${warning.line_no}行目: ` : ""}${warning.message}`)
      : ["- 大きな注意点は見つかりませんでした。ただし、実機での動作確認は別途必要です。"]),
  ];
  return lines.join("\n");
}

function formatLines(lines) {
  return lines.length ? lines.join(", ") : "-";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

sourceCode.value = samples[sampleSelect.value].code;
renderAnalysis(analyzeNcMacro(currentSourceName, sourceCode.value));
restoreActiveView();
