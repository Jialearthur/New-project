import { useEffect, useState } from "react";
import {
  askQuestion,
  deleteDocument,
  getMe,
  getSettings,
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
        <div>
          <p className="eyebrow">Project A</p>
          <h1>特定领域智能问答系统</h1>
          <p className="intro">
            面向企业制度文档的本地 RAG 课设演示版，支持文档建库、问答生成、引用展示和问答日志。
          </p>
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
            智能问答
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
        {activeView === "chat" ? <ChatPage token={token} /> : <AdminPage token={token} user={user} />}
      </main>
    </div>
  );
}

function LoginPage({ onLogin, error }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    await onLogin(username, password);
    setSubmitting(false);
  };

  return (
    <div className="login-shell">
      <div className="login-panel">
        <div>
          <p className="eyebrow">课程项目演示版</p>
          <h1>Project A 智能问答系统</h1>
          <p className="intro">
            使用本地模型 + 私有知识库实现企业制度问答，重点展示文档检索、答案生成和引用回溯。
          </p>
        </div>

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
      </div>
    </div>
  );
}

function ChatPage({ token }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [kbName, setKbName] = useState("企业制度知识库");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getSettings(token)
      .then((data) => setKbName(data.kbName))
      .catch(() => {});
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
      setResult(response);
      setHistory((current) => [{ question: question.trim(), ...response }, ...current].slice(0, 8));
      setQuestion("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="content-grid">
      <div className="panel hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">当前知识库</p>
          <h2>{kbName}</h2>
          <p>提问时系统会先检索相关制度片段，再基于证据生成答案，并展示引用来源用于核查。</p>
        </div>
        <form className="ask-form" onSubmit={submitQuestion}>
          <textarea
            rows={6}
            placeholder="例如：员工年假天数如何按照工龄计算？"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <div className="form-actions">
            <button type="submit" disabled={loading}>
              {loading ? "正在检索与生成..." : "开始问答"}
            </button>
          </div>
          {error ? <div className="error-box">{error}</div> : null}
        </form>
      </div>

      <div className="panel">
        <div className="section-title">
          <h3>最近一次回答</h3>
          {result ? <span>{result.latencyMs} ms</span> : null}
        </div>
        {result ? (
          <ResultCard result={result} />
        ) : (
          <div className="empty-state">上传文档后即可在这里发起提问，系统会返回答案和对应引用。</div>
        )}
      </div>

      <div className="panel">
        <div className="section-title">
          <h3>本地会话记录</h3>
          <span>仅前端展示最近 8 条</span>
        </div>
        {history.length ? (
          <div className="history-list">
            {history.map((item, index) => (
              <article key={`${item.question}-${index}`} className="history-item">
                <strong>{item.question}</strong>
                <p>{item.answer}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">尚无提问记录。</div>
        )}
      </div>
    </section>
  );
}

function ResultCard({ result }) {
  return (
    <div className="result-card">
      <div className={result.grounded ? "badge grounded" : "badge"}>{result.grounded ? "已命中证据" : "证据不足"}</div>
      <p className="answer-text">{result.answer}</p>
      <div className="citation-list">
        <h4>引用来源</h4>
        {result.citations.length ? (
          result.citations.map((citation, index) => (
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
          ))
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
          {loading ? <span>加载中...</span> : null}
        </div>
        <div className="inline-form">
          <input value={kbName} onChange={(event) => setKbName(event.target.value)} />
          <button onClick={saveKbName}>保存名称</button>
        </div>
        <form className="upload-form" onSubmit={handleUpload}>
          <label className="file-input">
            <span>上传文档</span>
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
                    暂无文档，请先上传制度文件。
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
