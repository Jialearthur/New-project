import { useEffect, useState } from "react";
import {
  askQuestion,
  deleteDocument,
  getMe,
  getSettings,
  healthCheck,
  listDocuments,
  listLogs,
  login,
  reindexDocument,
  updateSettings,
  uploadDocument,
} from "./api";

const DEMO_ACCOUNTS = [
  { username: "admin", password: "admin123", label: "管理员" },
  { username: "user", password: "user123", label: "演示用户" },
];

const SUGGESTED_QUESTIONS = [
  "高血压患者多久至少随访一次？",
  "发热门诊什么情况下要启动绿色通道？",
  "使用抗菌药物前需要先核对什么信息？",
];

function App() {
  const [token, setToken] = useState(localStorage.getItem("projectA_token") || "");
  const [user, setUser] = useState(null);
  const [activeView, setActiveView] = useState("chat");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }
    getMe(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("projectA_token");
        setToken("");
      });
  }, [token]);

  const handleLogin = async (username, password) => {
    setError("");
    try {
      const result = await login(username, password);
      localStorage.setItem("projectA_token", result.token);
      setToken(result.token);
      setUser(result.user);
    } catch (err) {
      setError(err.message);
    }
  };

  const logout = () => {
    localStorage.removeItem("projectA_token");
    setToken("");
    setUser(null);
  };

  if (!user) {
    return <LoginPage onLogin={handleLogin} error={error} />;
  }

  return (
    <div className="app-shell">
      <aside className="side-panel">
        <div className="brand-block">
          <div className="brand-mark">P</div>
          <div>
            <p className="eyebrow">Project A</p>
            <h1>医疗知识问答系统</h1>
            <p className="intro">
              面向门诊规范、分诊指引与用药提醒的本地 RAG 课设演示版，强调依据资料回答、引用可追溯和证据不足拒答。
            </p>
          </div>
        </div>

        <div className="account-card">
          <span className="account-role">{user.role === "admin" ? "管理员" : "用户"}</span>
          <strong>{user.displayName}</strong>
          <span className="account-id">@{user.username}</span>
        </div>

        <nav className="nav-stack">
          <button
            className={activeView === "chat" ? "nav-button active" : "nav-button"}
            onClick={() => setActiveView("chat")}
          >
            医疗问答
          </button>
          <button
            className={activeView === "admin" ? "nav-button active" : "nav-button"}
            onClick={() => setActiveView("admin")}
          >
            管理面板
          </button>
          <button className="nav-button ghost" onClick={logout}>
            退出登录
          </button>
        </nav>
      </aside>

      <main className="main-panel">
        <header className="workspace-header">
          <div>
            <p className="workspace-kicker">
              {activeView === "chat" ? "Clinical QA Workspace" : "Knowledge Base Control"}
            </p>
            <h2 className="workspace-title">
              {activeView === "chat" ? "一问一答医疗问答台" : "知识库管理面板"}
            </h2>
          </div>
          <div className="workspace-user">
            <span className="workspace-dot" />
            <span>{user.displayName}</span>
          </div>
        </header>

        {activeView === "chat" ? <ChatPage token={token} /> : <AdminPage token={token} user={user} />}
      </main>
    </div>
  );
}

function LoginPage({ onLogin, error }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [submitting, setSubmitting] = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking");

  useEffect(() => {
    healthCheck()
      .then(() => setBackendStatus("ready"))
      .catch(() => setBackendStatus("down"));
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    await onLogin(username, password);
    setSubmitting(false);
  };

  return (
    <div className="login-shell">
      <div className="login-panel">
        <div className="login-grid">
          <section className="login-copy">
            <p className="eyebrow">课程项目演示版</p>
            <h1>医疗知识问答系统</h1>
            <p className="login-text">
              使用本地模型与私有医疗资料构建问答系统，重点展示检索增强生成、来源引用和安全拒答。
            </p>
            <div className="status-cluster">
              <div className={backendStatus === "ready" ? "status-box" : "error-box"}>
                {backendStatus === "checking" ? "正在检测后端服务状态..." : null}
                {backendStatus === "ready" ? "后端服务连接正常，可以直接登录。" : null}
                {backendStatus === "down" ? "后端未连接。请先在 backend 目录启动 FastAPI 服务。" : null}
              </div>
            </div>
          </section>

          <section className="login-card">
            <form className="login-form" onSubmit={submit}>
              <label>
                用户名
                <input value={username} onChange={(event) => setUsername(event.target.value)} />
              </label>
              <label>
                密码
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </label>
              {error ? <div className="error-box">{error}</div> : null}
              <button type="submit" disabled={submitting}>
                {submitting ? "登录中..." : "进入系统"}
              </button>
            </form>

            <div className="demo-box">
              <strong>演示账号</strong>
              {DEMO_ACCOUNTS.map((account) => (
                <div key={account.username} className="demo-row">
                  <span>{account.label}</span>
                  <code>
                    {account.username} / {account.password}
                  </code>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function ChatPage({ token }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [kbName, setKbName] = useState("医疗知识库");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getSettings(token)
      .then((data) => setKbName(data.kbName))
      .catch(() => { });
  }, [token]);

  const submitQuestion = async (event) => {
    event.preventDefault();
    if (!question.trim()) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await askQuestion(token, question.trim());
      setResult({ question: question.trim(), ...response });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fillQuestion = (value) => {
    setQuestion(value);
    setError("");
  };

  return (
    <section className="medical-layout">
      <div className="hero-banner">
        <div className="hero-main">
          <p className="eyebrow green">当前知识库</p>
          <h2>{kbName}</h2>
          <p>
            本系统适用于医疗资料辅助查询。回答仅依据已上传文档生成，不替代医生诊断、处方与最终临床判断。
          </p>
        </div>
        <div className="hero-metrics">
          <div className="metric-card">
            <span>交互模式</span>
            <strong>Single Turn QA</strong>
          </div>
          <div className="metric-card">
            <span>回答约束</span>
            <strong>Evidence First</strong>
          </div>
          <div className="metric-card">
            <span>输出形式</span>
            <strong>答案 + 引用</strong>
          </div>
        </div>
      </div>

      <div className="qa-shell">
        <div className="qa-panel composer-panel">
          <div className="section-title">
            <h3>问题输入</h3>
            <span>Single request</span>
          </div>
          <form className="ask-form" onSubmit={submitQuestion}>
            <div className="input-caption">用一句自然语言输入你的临床流程、分诊或用药问题。</div>
            <textarea
              rows={5}
              placeholder="例如：发热门诊在什么情况下需要立即启动绿色通道？"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
            />
            <div className="suggestion-row">
              {SUGGESTED_QUESTIONS.map((item) => (
                <button
                  key={item}
                  type="button"
                  className="chip-button"
                  onClick={() => fillQuestion(item)}
                >
                  {item}
                </button>
              ))}
            </div>
            <div className="form-actions">
              <button type="submit" disabled={loading}>
                {loading ? "正在检索与生成..." : "提交问题"}
              </button>
            </div>
            {error ? <div className="error-box">{error}</div> : null}
          </form>

          <div className="safety-note">
            <strong>安全提示</strong>
            <p>系统仅做知识辅助检索，不输出最终诊断和处方决定。</p>
          </div>
        </div>

        <div className="qa-panel answer-panel">
          <div className="section-title">
            <h3>回答结果</h3>
            {result ? <span>{result.latencyMs} ms</span> : <span>Awaiting request</span>}
          </div>
          {result ? (
            <ResultCard result={result} />
          ) : (
            <div className="empty-state large-empty">
              输入一个医疗问题后，系统会返回单次回答结果，并在下方列出引用来源。
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function ResultCard({ result }) {
  return (
    <div className="result-card">
      <div className="message-block user-message">
        <div className="message-meta">
          <span className="message-role">Question</span>
        </div>
        <div className="question-card">{result.question}</div>
      </div>

      <div className="message-block assistant-message">
        <div className="message-meta">
          <span className="message-role">Answer</span>
          <div className={result.grounded ? "badge grounded" : "badge"}>
            {result.grounded ? "已命中证据" : "证据不足"}
          </div>
        </div>
        <p className="answer-text">{result.answer}</p>
      </div>

      <div className="sources-card">
        <div className="qa-label">引用来源</div>
        <div className="source-caption">每条来源都对应当前回答中用到的检索证据。</div>
        {result.citations.length ? (
          <div className="citation-list">
            {result.citations.map((citation, index) => (
              <div key={`${citation.filename}-${index}`} className="citation-item">
                <div className="citation-meta">
                  <strong>{citation.filename}</strong>
                  <span>
                    {citation.sectionPath || "未识别章节"}
                    {citation.pageNo ? ` / 第${citation.pageNo}页` : ""}
                  </span>
                </div>
                <p>{citation.snippet}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state compact">没有可用引用，系统已按证据不足处理。</div>
        )}
      </div>
    </div>
  );
}

function AdminPage({ token, user }) {
  const [kbName, setKbName] = useState("");
  const [documents, setDocuments] = useState([]);
  const [logs, setLogs] = useState([]);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    try {
      const [settingsData, documentData] = await Promise.all([getSettings(token), listDocuments(token)]);
      setKbName(settingsData.kbName);
      setDocuments(documentData);
      if (user.role === "admin") {
        const logData = await listLogs(token);
        setLogs(logData.slice(0, 10));
      }
    } catch (err) {
      setStatus(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [token]);

  const saveKbName = async () => {
    try {
      const result = await updateSettings(token, kbName);
      setKbName(result.kbName);
      setStatus("知识库名称已更新。");
    } catch (err) {
      setStatus(err.message);
    }
  };

  const handleUpload = async (event) => {
    event.preventDefault();
    if (!file) {
      setStatus("请先选择一个文件。");
      return;
    }
    setStatus("正在上传并建立索引...");
    try {
      await uploadDocument(token, file);
      setFile(null);
      event.target.reset();
      await refresh();
      setStatus("上传完成，索引已更新。");
    } catch (err) {
      setStatus(err.message);
    }
  };

  const handleReindex = async (documentId) => {
    setStatus("正在重建索引...");
    try {
      await reindexDocument(token, documentId);
      await refresh();
      setStatus("文档索引已重建。");
    } catch (err) {
      setStatus(err.message);
    }
  };

  const handleDelete = async (documentId) => {
    setStatus("正在删除文档...");
    try {
      await deleteDocument(token, documentId);
      await refresh();
      setStatus("文档已删除。");
    } catch (err) {
      setStatus(err.message);
    }
  };

  if (user.role !== "admin") {
    return (
      <section className="panel">
        <div className="section-title">
          <h3>管理面板</h3>
        </div>
        <div className="empty-state">当前账号不是管理员，只能使用问答页面。</div>
      </section>
    );
  }

  return (
    <section className="content-grid">
      <div className="panel">
        <div className="section-title">
          <h3>知识库设置</h3>
          {loading ? <span>Loading</span> : null}
        </div>
        <div className="inline-form">
          <input value={kbName} onChange={(event) => setKbName(event.target.value)} />
          <button onClick={saveKbName}>保存名称</button>
        </div>
        <form className="upload-form" onSubmit={handleUpload}>
          <label className="file-input">
            <span>上传医疗文档</span>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.html"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <button type="submit">上传并建库</button>
        </form>
        {status ? <div className="status-box">{status}</div> : null}
      </div>

      <div className="panel">
        <div className="section-title">
          <h3>文档列表</h3>
          <span>{documents.length} 份文档</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>文件名</th>
                <th>状态</th>
                <th>分块数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {documents.length ? (
                documents.map((document) => (
                  <tr key={document.id}>
                    <td>{document.filename}</td>
                    <td>{document.status}</td>
                    <td>{document.chunkCount}</td>
                    <td className="actions-cell">
                      <button className="small-button" onClick={() => handleReindex(document.id)}>
                        重建
                      </button>
                      <button className="small-button danger" onClick={() => handleDelete(document.id)}>
                        删除
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="empty-row">
                    暂无文档，请先上传医疗资料文件。
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <div className="section-title">
          <h3>最近问答日志</h3>
          <span>只展示最近 10 条</span>
        </div>
        {logs.length ? (
          <div className="history-list">
            {logs.map((log, index) => (
              <article key={`${log.createdAt}-${index}`} className="history-item">
                <strong>{log.question}</strong>
                <p>{log.answer}</p>
                <span>
                  {log.username} · {log.createdAt} · {log.latencyMs} ms
                </span>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">还没有问答日志。</div>
        )}
      </div>
    </section>
  );
}

export default App;
