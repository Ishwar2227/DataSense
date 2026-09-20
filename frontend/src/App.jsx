const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
import { useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import "./App.css";
const Icon = ({ name, size = 18 }) => {
  const paths = {
    logo: (
      <>
        <circle cx="12" cy="12" r="7" />
        <path d="M16.8 16.8 21 21M7.2 7.2 3 3" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V3m0 0L7 8m5-5 5 5M5 14v5h14v-5" />
      </>
    ),
    chart: (
      <>
        <path d="M3 18h18M5 15l4-5 4 3 6-8" />
        <circle cx="5" cy="15" r="1" />
        <circle cx="9" cy="10" r="1" />
        <circle cx="13" cy="13" r="1" />
        <circle cx="19" cy="5" r="1" />
      </>
    ),
    history: (
      <>
        <circle cx="12" cy="12" r="8" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    settings: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19 12a7.5 7.5 0 0 0-.1-1.2l2-1.5-2-3.4-2.3 1A8 8 0 0 0 14.5 6L14 3h-4l-.5 3a8 8 0 0 0-2.1 1l-2.3-1-2 3.4 2 1.5A7.5 7.5 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.5 2 3.4 2.3-1a8 8 0 0 0 2.1 1l.5 3h4l.5-3a8 8 0 0 0 2.1-1l2.3 1 2-3.4-2-1.5c.1-.4.1-.8.1-1.2Z" />
      </>
    ),
    database: (
      <>
        <ellipse cx="12" cy="5" rx="7" ry="3" />
        <path d="M5 5v7c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 12v7c0 1.7 3.1 3 7 3s7-1.3 7-3v-7" />
      </>
    ),
    calendar: (
      <>
        <rect x="4" y="5" width="16" height="15" rx="2" />
        <path d="M8 3v4m8-4v4M4 10h16" />
      </>
    ),
    tag: (
      <>
        <path d="M20 13 13 20 4 11V4h7l9 9Z" />
        <circle cx="8.5" cy="8.5" r="1" />
      </>
    ),
    broom: (
      <>
        <path d="m4 20 7-7m0 0 2-7 7-2-2 7-7 2Zm-2 2 4-4" />
      </>
    ),
    alert: (
      <>
        <path d="M12 3 2.8 20h18.4L12 3Z" />
        <path d="M12 9v4m0 3h.01" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    table: (
      <>
        <rect x="3" y="4" width="18" height="16" rx="1" />
        <path d="M3 9h18M9 9v11" />
      </>
    )
  };

  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
};

const compactNumber = (n) =>
  Number.isFinite(Number(n))
    ? new Intl.NumberFormat(undefined, {
        notation: "compact",
        maximumFractionDigits: 1
      }).format(n)
    : "—";

const readableValue = (value) =>
  typeof value === "number"
    ? value.toLocaleString(undefined, {
        maximumFractionDigits: 2
      })
    : value ?? "—";

const EmptyAnalysis = ({ children }) => (
  <div className="empty-analysis">
    <Icon name="alert" size={17} />
    <p>{children}</p>
  </div>
);

const AnswerContent = ({ answer }) => {
  const formatInline = (text) =>
    text.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
      part.startsWith("**") && part.endsWith("**") ? (
        <strong key={index}>{part.slice(2, -2)}</strong>
      ) : (
        part
      )
    );

  const elements = [];
  let bullets = [];

  const flushBullets = () => {
    if (bullets.length) {
      elements.push(
        <ul key={`bullets-${elements.length}`}>
          {bullets.map((item, index) => (
            <li key={index}>{formatInline(item)}</li>
          ))}
        </ul>
      );

      bullets = [];
    }
  };

  String(answer)
    .replace(/\\n/g, "\n")
    .split(/\r?\n/)
    .forEach((line) => {
      const bullet = line.match(/^\s*(?:[-*•])\s+(.+)$/);

      if (bullet) {
        bullets.push(bullet[1]);
        return;
      }

      flushBullets();

      if (line.trim()) {
        elements.push(
          <p key={`line-${elements.length}`}>
            {formatInline(line)}
          </p>
        );
      }
    });

  flushBullets();

  return <>{elements}</>;
};

function App() {
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [cleaningOpen, setCleaningOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("trends");

  const [questionLoading, setQuestionLoading] = useState("");
  const [questionResult, setQuestionResult] = useState(null);
  const [questionError, setQuestionError] = useState("");
  const [customQuestion, setCustomQuestion] = useState("");

  const insights = result?.insights;

  const selectedColumns = insights?.selected_columns || {};

  const {
    date_col: dateCol,
    value_col: valueCol,
    group_col: groupCol
  } = selectedColumns;

  const trend = insights?.trend || [];
  const contributors = insights?.top_contributors || [];
  const outliers = insights?.outliers || [];

  // =========================================================
  // FILE SELECTION
  // =========================================================

  const setSelectedFile = (selectedFile) => {
    if (!selectedFile) return;

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setError("Choose a CSV file to continue.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setResult(null);
    setError("");
    setCleaningOpen(false);
    setQuestionResult(null);
    setQuestionError("");
    setCustomQuestion("");
  };

  // =========================================================
  // ANALYZE FILE
  // =========================================================

  const analyzeFile = async () => {
    if (!file) {
      return setError(
        "Choose a CSV file before starting analysis."
      );
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(
        `${API_URL}/api/insights`,
        {
          method: "POST",
          body: formData
        }
      );

      if (!response.ok) {
        const data = await response
          .json()
          .catch(() => null);

        throw new Error(
          data?.detail ||
            `The analysis service returned an error (${response.status}).`
        );
      }

      setResult(await response.json());
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "We couldn't analyze this CSV. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // ASK QUESTION
  // =========================================================

  const askQuestion = async (
    questionId = null,
    customQuestionText = ""
  ) => {
    if (!file) {
      setQuestionError(
        "Choose a CSV file before asking a question."
      );
      return;
    }

    const typedQuestion = customQuestionText.trim();

    if (!questionId && !typedQuestion) {
      setQuestionError(
        "Type a question before asking."
      );
      return;
    }

    setQuestionLoading(questionId || "custom");
    setQuestionResult(null);
    setQuestionError("");

    const formData = new FormData();

    formData.append("file", file);

    if (questionId) {
      formData.append("question_id", questionId);
    } else {
      formData.append("question", typedQuestion);
    }

    try {
      const response = await fetch(
        `${API_URL}/api/question`,
        {
          method: "POST",
          body: formData
        }
      );

      if (!response.ok) {
        const data = await response
          .json()
          .catch(() => null);

        throw new Error(
          data?.detail ||
            `The question service returned an error (${response.status}).`
        );
      }

      const data = await response.json();

      if (!data?.answer) {
        throw new Error(
          "The question service did not return an answer."
        );
      }

      setQuestionResult(data);
    } catch (err) {
      console.error(err);

      setQuestionError(
        err.message ||
          "We couldn't answer that question. Please try again."
      );
    } finally {
      setQuestionLoading("");
    }
  };

  // =========================================================
  // KEYBOARD HANDLER FOR CUSTOM QUESTION
  // =========================================================

  const handleCustomQuestionKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();

      askQuestion(null, customQuestion);
    }
  };

  const tabs = [
    ["trends", "Trends", "chart"],
    ["contributors", "Top contributors", "chart"],
    ["outliers", "Outliers", "alert"],
    ["preview", "Data preview", "table"]
  ];

  const questions = [
    ["why_change", "Why did the value change?"],
    ["top_group", "Which group changed the most?"],
    ["anomalies", "Are there any anomalies?"]
  ];

  const changes = result?.cleaning_log || [];

  return (
    <div className="app-shell">

      {/* =====================================================
          SIDEBAR
      ===================================================== */}

      <aside className="sidebar">

        <div className="brand">
          <span className="brand-mark">
            <Icon name="logo" size={28} />
          </span>

          <span>DataSense</span>
        </div>

        <p className="brand-note">
          Find what matters
          <br />
          in your data.
        </p>

        <nav
          className="side-nav"
          aria-label="Primary navigation"
        >
          <a
            className="active"
            href="#analyze"
          >
            <Icon name="chart" />
            Analyze
          </a>

          <a href="#history">
            <Icon name="history" />
            History
          </a>

          <a href="#examples">
            <Icon name="table" />
            Examples
          </a>

          <a href="#settings">
            <Icon name="settings" />
            Settings
          </a>
        </nav>

        <div className="sidebar-footer">
          <p>
            Turning messy data into meaningful insights.
          </p>

          <span>
            v0.1.0 <i /> API online
          </span>
        </div>

      </aside>

      {/* =====================================================
          MAIN WORKSPACE
      ===================================================== */}

      <main
        className="workspace"
        id="analyze"
      >

        {/* ===================================================
            HEADER
        =================================================== */}

        <header className="page-header">

          <div>

            <p className="eyebrow">
              Upload <span>→</span> Analyze{" "}
              <span>→</span> Discover
            </p>

            <h1>
              Your data has a <em>story.</em>
            </h1>

            <p className="page-intro">
              Upload your CSV file and let DataSense
              clean it, understand it, and find what
              matters.
            </p>

          </div>

          <p className="header-aside">
            Real data.
            <br />
            Real insights.
          </p>

        </header>

        {/* ===================================================
            UPLOAD PANEL
        =================================================== */}

        <section
          className="upload-panel"
          aria-label="Upload dataset"
        >

          <div
            className={`drop-zone ${
              dragging ? "is-dragging" : ""
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);

              setSelectedFile(
                e.dataTransfer.files?.[0]
              );
            }}
            onClick={() =>
              inputRef.current?.click()
            }
            role="button"
            tabIndex="0"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                inputRef.current?.click();
              }
            }}
          >

            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              onChange={(e) =>
                setSelectedFile(
                  e.target.files?.[0]
                )
              }
            />

            <span className="upload-glyph">
              <Icon name="upload" size={25} />
            </span>

            <strong>
              {file
                ? "Replace selected CSV"
                : "Drag & drop your CSV file here"}
            </strong>

            <small>
              {file
                ? file.name
                : "or click to browse"}
            </small>

            <p>
              Supports CSV files up to 100 MB
            </p>

          </div>

          <div className="file-details">

            {file ? (
              <>
                <span className="file-icon">
                  <Icon name="table" size={19} />
                </span>

                <div>
                  <strong>{file.name}</strong>

                  <p>
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                    {" · "}
                    ready to analyze
                  </p>
                </div>
              </>
            ) : (
              <>
                <span className="file-icon muted">
                  <Icon name="table" size={19} />
                </span>

                <div>
                  <strong>
                    No dataset selected
                  </strong>

                  <p>
                    Select a CSV to begin analysis.
                  </p>
                </div>
              </>
            )}

          </div>

          <button
            className="primary-button"
            onClick={analyzeFile}
            disabled={!file || loading}
          >
            {loading ? (
              <>
                <span className="button-loader" />
                Analyzing data
              </>
            ) : (
              <>
                Analyze data <span>→</span>
              </>
            )}
          </button>

        </section>

        {/* ===================================================
            ERROR
        =================================================== */}

        {error && (
          <div
            className="message error-message"
            role="alert"
          >
            <Icon name="alert" />
            {error}
          </div>
        )}

        {/* ===================================================
            LOADING
        =================================================== */}

        {loading && (
          <section className="loading-panel">

            <div className="loading-rule">
              <i />
            </div>

            <strong>
              Preparing your analysis
            </strong>

            <p>
              Reading your dataset, cleaning fields,
              and looking for meaningful patterns.
            </p>

          </section>
        )}

        {/* ===================================================
            RESULTS
        =================================================== */}

        {result && (
          <div className="results">

            {/* ===============================================
                CLEANING REPORT
            =============================================== */}

            <section className="cleaning-report">

              <div className="report-icon">
                <Icon name="broom" size={21} />
              </div>

              <div className="report-copy">

                <div>
                  <h2>Cleaning report</h2>

                  <span className="change-count">
                    {changes.length}{" "}
                    {changes.length === 1
                      ? "change"
                      : "changes"}
                  </span>
                </div>

                <p>
                  DataSense cleaned your data and
                  fixed common issues.
                </p>

              </div>

              <button
                className="text-button"
                onClick={() =>
                  setCleaningOpen(
                    !cleaningOpen
                  )
                }
              >
                {cleaningOpen
                  ? "Hide details"
                  : "View details"}

                <span>
                  {cleaningOpen ? "⌃" : "⌄"}
                </span>
              </button>

              {cleaningOpen && (
                <div className="cleaning-details">

                  {changes.length ? (
                    changes.map(
                      (change, index) => (
                        <p key={index}>
                          <Icon
                            name={
                              /skipped|failed|fallback/i.test(
                                change
                              )
                                ? "alert"
                                : "check"
                            }
                            size={15}
                          />

                          {change}
                        </p>
                      )
                    )
                  ) : (
                    <p>
                      <Icon
                        name="check"
                        size={15}
                      />

                      No cleaning issues were
                      detected.
                    </p>
                  )}

                </div>
              )}

            </section>

            {/* ===============================================
                METRIC CARDS
            =============================================== */}

            <section
              className="metric-grid"
              aria-label="Dataset summary"
            >

              <article className="metric-card">

                <span className="metric-icon blue">
                  <Icon name="database" />
                </span>

                <div>
                  <p>Dataset</p>

                  <strong>
                    {result.filename ||
                      file?.name ||
                      "Uploaded CSV"}
                  </strong>

                  <small>
                    {file
                      ? `${(
                          file.size /
                          1024 /
                          1024
                        ).toFixed(2)} MB file`
                      : "Analysis complete"}
                  </small>
                </div>

              </article>

              <article className="metric-card">

                <span className="metric-icon blue">
                  <Icon name="calendar" />
                </span>

                <div>
                  <p>Date column</p>

                  <strong>
                    {dateCol ||
                      "Not detected"}
                  </strong>

                  <small>
                    {dateCol
                      ? "Used for trend analysis"
                      : "Trend unavailable"}
                  </small>
                </div>

              </article>

              <article className="metric-card">

                <span className="metric-icon orange">
                  <Icon name="database" />
                </span>

                <div>
                  <p>Value column</p>

                  <strong>
                    {valueCol ||
                      "Not detected"}
                  </strong>

                  <small>
                    {valueCol
                      ? "Used for analysis"
                      : "Analysis limited"}
                  </small>
                </div>

              </article>

              <article className="metric-card">

                <span className="metric-icon charcoal">
                  <Icon name="tag" />
                </span>

                <div>
                  <p>Group column</p>

                  <strong>
                    {groupCol ||
                      "Not detected"}
                  </strong>

                  <small>
                    {groupCol
                      ? "Used for contributors"
                      : "Group analysis unavailable"}
                  </small>
                </div>

              </article>

            </section>

            {/* ===============================================
                ANALYSIS TABS
            =============================================== */}

            <div
              className="analysis-tabs"
              role="tablist"
            >

              {tabs.map(
                ([id, label, icon]) => (
                  <button
                    key={id}
                    role="tab"
                    aria-selected={
                      activeTab === id
                    }
                    className={
                      activeTab === id
                        ? "selected"
                        : ""
                    }
                    onClick={() =>
                      setActiveTab(id)
                    }
                  >
                    <Icon
                      name={icon}
                      size={16}
                    />
                    {label}
                  </button>
                )
              )}

            </div>

            {/* ===============================================
                TRENDS
            =============================================== */}

            {activeTab === "trends" && (
              <section className="analysis-card">

                <div className="card-heading">

                  <div>
                    <h2>
                      {valueCol || "Value"} trend
                    </h2>

                    <p>
                      {dateCol
                        ? `Monthly totals by ${dateCol}`
                        : "Trend analysis"}
                    </p>
                  </div>

                  <span className="quiet-label">
                    Monthly
                  </span>

                </div>

                {trend.length ? (
                  <div className="chart-wrap">

                    <ResponsiveContainer
                      width="100%"
                      height={320}
                    >

                      <LineChart
                        data={trend}
                        margin={{
                          top: 16,
                          right: 15,
                          bottom: 0,
                          left: 4
                        }}
                      >

                        <CartesianGrid
                          vertical={false}
                          stroke="#ebe7e1"
                        />

                        <XAxis
                          dataKey="month"
                          tick={{
                            fill: "#77736e",
                            fontSize: 11
                          }}
                          tickLine={false}
                          axisLine={false}
                          minTickGap={26}
                        />

                        <YAxis
                          tickFormatter={
                            compactNumber
                          }
                          tick={{
                            fill: "#77736e",
                            fontSize: 11
                          }}
                          tickLine={false}
                          axisLine={false}
                          width={48}
                        />

                        <Tooltip
                          formatter={(value) => [
                            readableValue(value),
                            valueCol || "Value"
                          ]}
                          contentStyle={{
                            border: "1px solid #e2ddd5",
                            borderRadius: 8,
                            boxShadow:
                              "0 7px 20px rgba(42,35,27,.08)"
                          }}
                        />

                        <Line
                          type="monotone"
                          dataKey={valueCol}
                          stroke="#a45520"
                          strokeWidth={2.4}
                          dot={{
                            r: 3,
                            fill: "#a45520",
                            strokeWidth: 0
                          }}
                          activeDot={{
                            r: 5
                          }}
                        />

                      </LineChart>

                    </ResponsiveContainer>

                  </div>
                ) : (
                  <EmptyAnalysis>
                    {dateCol
                      ? "No monthly trend values were returned for this dataset."
                      : "Trend analysis isn't available because no date column was detected."}
                  </EmptyAnalysis>
                )}

              </section>
            )}

            {/* ===============================================
                CONTRIBUTORS
            =============================================== */}

            {activeTab === "contributors" && (
              <section className="analysis-card">

                <div className="card-heading">

                  <div>
                    <h2>
                      Top contributors to change
                    </h2>

                    <p>
                      {groupCol
                        ? `Groups in ${groupCol} with the largest change`
                        : "Group analysis"}
                    </p>
                  </div>

                  <span className="quiet-label">
                    Latest month
                  </span>

                </div>

                {contributors.length ? (
                  <div className="chart-wrap">

                    <ResponsiveContainer
                      width="100%"
                      height={Math.max(
                        260,
                        contributors.slice(
                          0,
                          10
                        ).length * 38
                      )}
                    >

                      <BarChart
                        data={contributors.slice(
                          0,
                          10
                        )}
                        layout="vertical"
                        margin={{
                          top: 5,
                          right: 22,
                          bottom: 4,
                          left: 15
                        }}
                      >

                        <CartesianGrid
                          horizontal={false}
                          stroke="#ebe7e1"
                        />

                        <XAxis
                          type="number"
                          tickFormatter={
                            compactNumber
                          }
                          tick={{
                            fill: "#77736e",
                            fontSize: 11
                          }}
                          tickLine={false}
                          axisLine={false}
                        />

                        <YAxis
                          type="category"
                          dataKey={groupCol}
                          width={125}
                          tick={{
                            fill: "#302d29",
                            fontSize: 12
                          }}
                          tickLine={false}
                          axisLine={false}
                        />

                        <Tooltip
                          formatter={(value) => [
                            readableValue(value),
                            "Change"
                          ]}
                          contentStyle={{
                            border:
                              "1px solid #e2ddd5",
                            borderRadius: 8
                          }}
                        />

                        <Bar
                          dataKey="change"
                          fill="#4383c9"
                          radius={[
                            0,
                            3,
                            3,
                            0
                          ]}
                        />

                      </BarChart>

                    </ResponsiveContainer>

                  </div>
                ) : (
                  <EmptyAnalysis>
                    {groupCol && dateCol
                      ? "No contributor changes were returned for the latest period."
                      : "Contributor analysis requires both a date column and a grouping column."}
                  </EmptyAnalysis>
                )}

              </section>
            )}

            {/* ===============================================
                OUTLIERS
            =============================================== */}

            {activeTab === "outliers" && (
              <section className="analysis-card">

                <div className="card-heading">

                  <div>
                    <h2>
                      Outlier detection{" "}
                      <span className="change-count danger">
                        {insights?.outlier_count ||
                          0}{" "}
                        outliers
                      </span>
                    </h2>

                    <p>
                      Records that look unusually
                      high or low compared with
                      the rest.
                    </p>
                  </div>

                </div>

                {outliers.length ? (
                  <div className="table-scroll">

                    <table>

                      <thead>
                        <tr>
                          <th>Record</th>
                          <th>
                            {valueCol ||
                              "Value"}
                          </th>

                          {groupCol && (
                            <th>
                              {groupCol}
                            </th>
                          )}

                          <th>
                            Z-score
                          </th>
                        </tr>
                      </thead>

                      <tbody>

                        {outliers
                          .slice()
                          .sort(
                            (a, b) =>
                              Math.abs(
                                b.z_score
                              ) -
                              Math.abs(
                                a.z_score
                              )
                          )
                          .map(
                            (
                              outlier,
                              index
                            ) => {

                              const recordId =
                                outlier.InvoiceNo ??
                                outlier[
                                  "Invoice No"
                                ] ??
                                outlier[
                                  "Order ID"
                                ] ??
                                outlier.Order_ID ??
                                outlier[
                                  "Row ID"
                                ] ??
                                outlier[
                                  "Customer ID"
                                ] ??
                                `Row ${
                                  index + 1
                                }`;

                              const description =
                                outlier.Description ??
                                outlier[
                                  "Product Name"
                                ] ??
                                outlier.Product_Name;

                              return (
                                <tr
                                  key={index}
                                >

                                  <td>
                                    <strong>
                                      {
                                        recordId
                                      }
                                    </strong>

                                    {description && (
                                      <small>
                                        {
                                          description
                                        }
                                      </small>
                                    )}
                                  </td>

                                  <td>
                                    {readableValue(
                                      valueCol
                                        ? outlier[
                                            valueCol
                                          ]
                                        : null
                                    )}
                                  </td>

                                  {groupCol && (
                                    <td>
                                      {outlier[
                                        groupCol
                                      ] ?? "—"}
                                    </td>
                                  )}

                                  <td>
                                    <span className="z-score">
                                      {Number(
                                        outlier.z_score
                                      ).toFixed(
                                        2
                                      )}
                                    </span>
                                  </td>

                                </tr>
                              );
                            }
                          )}

                      </tbody>

                    </table>

                  </div>
                ) : (
                  <EmptyAnalysis>
                    {valueCol
                      ? "Analysis completed: no unusual records were detected."
                      : "Outlier detection requires a usable numeric value column."}
                  </EmptyAnalysis>
                )}

              </section>
            )}

            {/* ===============================================
                DATA PREVIEW
            =============================================== */}

            {activeTab === "preview" && (
              <section className="analysis-card">

                <div className="card-heading">

                  <div>
                    <h2>
                      Data preview
                    </h2>

                    <p>
                      A quick look at the
                      cleaned rows.
                    </p>
                  </div>

                </div>

                <EmptyAnalysis>
                  A row-level preview is not
                  included in the current
                  analysis response. Your
                  uploaded data and analysis
                  results remain unchanged.
                </EmptyAnalysis>

              </section>
            )}

            {/* ===============================================
                ASK DATA
            =============================================== */}

            <section
              className="ask-data-card"
              aria-labelledby="ask-data-title"
            >

              <div className="card-heading">

                <div>
                  <h2 id="ask-data-title">
                    Ask Data
                  </h2>

                  <p>
                    Choose a question to get a
                    focused answer from this
                    dataset.
                  </p>
                </div>

              </div>

              {/* =============================================
                  FIXED QUESTIONS
              ============================================= */}

              <div className="question-actions">

                {questions.map(
                  ([id, label]) => (
                    <button
                      key={id}
                      className="question-button"
                      onClick={() =>
                        askQuestion(id)
                      }
                      disabled={Boolean(
                        questionLoading
                      )}
                    >

                      {questionLoading ===
                      id ? (
                        <>
                          <span className="button-loader" />
                          Analyzing question...
                        </>
                      ) : (
                        label
                      )}

                    </button>
                  )
                )}

              </div>

              {/* =============================================
                  CUSTOM QUESTION
              ============================================= */}

              <div className="custom-question">

                <label htmlFor="custom-question-input">
                  Or ask your own question
                </label>

                <div className="custom-question-row">

                  <input
                    id="custom-question-input"
                    type="text"
                    value={customQuestion}
                    onChange={(e) =>
                      setCustomQuestion(
                        e.target.value
                      )
                    }
                    onKeyDown={
                      handleCustomQuestionKeyDown
                    }
                    placeholder="e.g. Why did sales fall?"
                    disabled={Boolean(
                      questionLoading
                    )}
                  />

                  <button
                    className="primary-button"
                    onClick={() =>
                      askQuestion(
                        null,
                        customQuestion
                      )
                    }
                    disabled={
                      !customQuestion.trim() ||
                      Boolean(questionLoading)
                    }
                  >

                    {questionLoading ===
                    "custom" ? (
                      <>
                        <span className="button-loader" />
                        Asking...
                      </>
                    ) : (
                      <>
                        Ask Data <span>→</span>
                      </>
                    )}

                  </button>

                </div>

              </div>

              {/* =============================================
                  QUESTION ERROR
              ============================================= */}

              {questionError && (
                <div
                  className="message error-message question-message"
                  role="alert"
                >
                  <Icon name="alert" />
                  {questionError}
                </div>
              )}

              {/* =============================================
                  QUESTION ANSWER
              ============================================= */}

              {questionResult && (
                <article className="answer-card">

                  <p className="answer-question">
                    {questionResult.question}
                  </p>

                  <div className="answer-copy">
                    <AnswerContent
                      answer={
                        questionResult.answer
                      }
                    />
                  </div>

                </article>
              )}

            </section>

          </div>
        )}

      </main>

    </div>
  );
}

export default App;