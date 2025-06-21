import React, { useState, useEffect } from "react";
import {
  Layout,
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Select,
  DatePicker,
  Tag,
  Space,
  Typography,
  Alert,
  Spin,
  message,
  Progress,
  Timeline,
  Calendar,
  Badge,
  Tooltip,
} from "antd";
import {
  UserOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  TrophyOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  MailOutlined,
} from "@ant-design/icons";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";
import dayjs from "dayjs";

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const ParentDashboard = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [children, setChildren] = useState([]);
  const [selectedChild, setSelectedChild] = useState(null);
  const [attendanceData, setAttendanceData] = useState([]);
  const [monthlyData, setMonthlyData] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [dateRange, setDateRange] = useState([
    dayjs().subtract(30, "day"),
    dayjs(),
  ]);
  const [stats, setStats] = useState({
    totalDays: 0,
    presentDays: 0,
    absentDays: 0,
    lateDays: 0,
    attendanceRate: 0,
  });

  useEffect(() => {
    const fetchChildren = async () => {
      try {
        setLoading(true);

        // Check if user is a parent
        if (!user || user.role !== "parent") {
          message.error("Access denied: Only parents can view this dashboard");
          setChildren([]);
          return;
        }

        // Fetch children using the parent-specific endpoint
        const response = await api.get(`/students/parent/${user.id}`);

        // Handle the response format
        const children = Array.isArray(response.data)
          ? response.data
          : response.data?.data || [];

        setChildren(children);

        if (children.length > 0) {
          // Use 'id' field, not '_id'
          setSelectedChild(children[0].id);

          // Fetch alerts after children are loaded
          fetchAlerts(children);
        } else {
          message.info("No children found for this parent account");
          // Clear alerts if no children
          setAlerts([]);
        }
      } catch (error) {
        console.error("Error fetching children:", error);

        if (error.response?.status === 403) {
          message.error("Access denied: You can only view your own children");
        } else if (error.response?.status === 404) {
          message.error("Parent account not found");
        } else {
          message.error(error.message || "Failed to fetch student information");
        }

        setChildren([]); // Set to empty array on error
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchChildren();
    }
  }, [user]);

  useEffect(() => {
    if (selectedChild) {
      fetchAttendanceData();
      fetchMonthlyData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedChild, dateRange]);

  const fetchAttendanceData = async () => {
    if (!selectedChild) return;

    try {
      setLoading(true);

      const [startDate, endDate] = dateRange;
      const response = await api.get(
        `/attendance/student/${selectedChild}/history`,
        {
          params: {
            start_date: startDate.format("YYYY-MM-DD"),
            end_date: endDate.format("YYYY-MM-DD"),
          },
        },
      );

      const attendance =
        response.data?.data?.attendance_history ||
        response.data?.attendance_history ||
        [];

      setAttendanceData(attendance);

      // Calculate statistics - handle different data structures
      const totalDays = attendance.length;

      const getStatus = (record) => {
        // Try different possible structures
        return (
          record.status ||
          record.attendance?.status ||
          record.overall_status ||
          "unknown"
        );
      };

      const presentDays = attendance.filter(
        (a) => getStatus(a) === "present",
      ).length;
      const absentDays = attendance.filter(
        (a) => getStatus(a) === "absent" || getStatus(a) === "excused",
      ).length;
      const lateDays = attendance.filter((a) => getStatus(a) === "late").length;

      const allStatuses = attendance.map((a) => getStatus(a));
      const uniqueStatuses = [...new Set(allStatuses)];

      const attendanceRate =
        totalDays > 0 ? (presentDays / totalDays) * 100 : 0;

      setStats({
        totalDays,
        presentDays,
        absentDays,
        lateDays,
        attendanceRate: Math.round(attendanceRate),
      });
    } catch (error) {
      message.error("Failed to fetch attendance data");
      console.error("Error fetching attendance:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMonthlyData = async () => {
    if (!selectedChild) return;

    try {
      // TODO: Implement monthly calendar endpoint for individual students
      setMonthlyData({});
    } catch (error) {
      console.error("Error fetching monthly data:", error);
    }
  };

  const fetchAlerts = async (childrenList = children) => {
    try {
      const response = await api.get("/alerts");

      // Handle the response format: data is directly in response.data (not response.data.alerts)
      let alertsData = Array.isArray(response.data)
        ? response.data
        : response.data?.data || [];

      // If response has the structure { data: [...], message: "...", success: true }
      if (
        response.data &&
        response.data.data &&
        Array.isArray(response.data.data)
      ) {
        alertsData = response.data.data;
      }

      // Get current parent's children info for filtering
      const childrenIds = childrenList.map((child) => child.id);
      const childrenNames = childrenList.map(
        (child) => `${child.first_name} ${child.last_name}`,
      );

      // Filter alerts for current parent's children
      const parentAlerts = alertsData
        .filter((alert) => {
          // Check if alert is relevant to parent (absence, late, or parent notification)
          const isRelevantType =
            alert.type === "absence" ||
            alert.type === "late" ||
            alert.type === "parent_notification" ||
            alert.type === "pattern"; // Include pattern alerts as they can be relevant for parents

          // Check if alert is for one of parent's children
          // Try both student_id and student_name matching (case insensitive)
          const isForParentChild =
            (alert.student_id && childrenIds.includes(alert.student_id)) ||
            (alert.student_name &&
              childrenNames.some(
                (name) =>
                  name.toLowerCase() === alert.student_name.toLowerCase(),
              ));
          const shouldInclude = isRelevantType && isForParentChild;
          return shouldInclude;
        })
        .slice(0, 5);

      setAlerts(parentAlerts);
    } catch (error) {
      console.error("Error fetching alerts:", error);
    }
  };

  const getAttendanceColumns = () => [
    {
      title: "Date",
      dataIndex: "date",
      key: "date",
      render: (date) => dayjs(date).format("MMM D, YYYY"),
      sorter: (a, b) => dayjs(a.date).unix() - dayjs(b.date).unix(),
    },
    {
      title: "Class",
      dataIndex: "class_name",
      key: "class_name",
      render: (className) => className || "General Class",
    },
    {
      title: "Status",
      key: "status",
      render: (_, record) => {
        // Use the same logic as stats calculation
        const status =
          record.status ||
          record.attendance?.status ||
          record.overall_status ||
          "unknown";
        const config = {
          present: {
            color: "green",
            icon: <CheckCircleOutlined />,
            text: "Present",
          },
          absent: {
            color: "red",
            icon: <ExclamationCircleOutlined />,
            text: "Absent",
          },
          late: {
            color: "orange",
            icon: <ClockCircleOutlined />,
            text: "Late",
          },
          excused: {
            color: "red",
            icon: <ExclamationCircleOutlined />,
            text: "Absent",
          },
        };

        const { color, icon, text } = config[status] || config.absent;

        return (
          <Tag color={color} icon={icon}>
            {text}
          </Tag>
        );
      },
    },
    {
      title: "Time",
      dataIndex: "marked_at",
      key: "marked_at",
      render: (time) => (time ? dayjs(time).format("HH:mm:ss") : "-"),
    },
    {
      title: "Notes",
      dataIndex: "notes",
      key: "notes",
      render: (notes) => notes || "-",
    },
  ];

  const getCalendarDateCellRender = (date) => {
    const dateStr = date.format("YYYY-MM-DD");
    const dayData = monthlyData[dateStr];

    if (!dayData) return null;

    const statusConfig = {
      present: { color: "success", text: "P" },
      absent: { color: "error", text: "A" },
      late: { color: "warning", text: "L" },
    };

    return (
      <div style={{ fontSize: "12px" }}>
        {dayData.map((record, index) => {
          const config = statusConfig[record.status] || statusConfig.absent;
          return (
            <Badge
              key={index}
              status={config.color}
              text={config.text}
              style={{ display: "block", fontSize: "10px" }}
            />
          );
        })}
      </div>
    );
  };

  const selectedChildInfo =
    children && children.find((child) => child.id === selectedChild);

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          background: "#fff",
          padding: "0 24px",
          borderBottom: "1px solid #f0f0f0",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Space>
          <UserOutlined style={{ fontSize: "24px", color: "#1890ff" }} />
          <Title level={4} style={{ margin: 0 }}>
            Parent Dashboard
          </Title>
        </Space>

        <Space>
          <Text>Welcome, {user?.name}!</Text>
          <Button onClick={logout}>Logout</Button>
        </Space>
      </Header>

      <Content style={{ padding: "24px" }}>
        {/* Child Selection and Date Range */}
        <Row gutter={[16, 16]} style={{ marginBottom: "24px" }}>
          <Col xs={24} sm={12} md={8}>
            <Card size="small">
              <Space direction="vertical" style={{ width: "100%" }}>
                <Text strong>Select Child:</Text>
                <Select
                  style={{ width: "100%" }}
                  value={selectedChild}
                  onChange={setSelectedChild}
                  placeholder="Choose a child"
                >
                  {children &&
                    children.map((child) => (
                      <Option key={child.id} value={child.id}>
                        {child.first_name} {child.last_name} - Grade{" "}
                        {child.grade}
                      </Option>
                    ))}
                </Select>
              </Space>
            </Card>
          </Col>

          <Col xs={24} sm={12} md={8}>
            <Card size="small">
              <Space direction="vertical" style={{ width: "100%" }}>
                <Text strong>Date Range:</Text>
                <RangePicker
                  style={{ width: "100%" }}
                  value={dateRange}
                  onChange={setDateRange}
                  disabledDate={(date) => date.isAfter(dayjs())}
                />
              </Space>
            </Card>
          </Col>

          <Col xs={24} sm={24} md={8}>
            <Card size="small">
              <Button
                type="primary"
                icon={<BarChartOutlined />}
                onClick={fetchAttendanceData}
                disabled={!selectedChild}
                style={{ width: "100%" }}
              >
                Generate Report
              </Button>
            </Card>
          </Col>
        </Row>

        {/* Student Info & Statistics */}
        {selectedChildInfo && (
          <Alert
            message={`Attendance Report for ${selectedChildInfo.first_name} ${selectedChildInfo.last_name}`}
            description={`Grade ${selectedChildInfo.grade} • Student ID: ${selectedChildInfo.student_id}`}
            type="info"
            icon={<UserOutlined />}
            showIcon
            style={{ marginBottom: "24px" }}
          />
        )}

        <Row gutter={[16, 16]} style={{ marginBottom: "24px" }}>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="Total Days"
                value={stats.totalDays}
                prefix={<CalendarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="Present"
                value={stats.presentDays}
                valueStyle={{ color: "#3f8600" }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="Absent"
                value={stats.absentDays}
                valueStyle={{ color: "#cf1322" }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="Attendance Rate"
                value={stats.attendanceRate}
                suffix="%"
                valueStyle={{
                  color:
                    stats.attendanceRate >= 90
                      ? "#3f8600"
                      : stats.attendanceRate >= 80
                      ? "#faad14"
                      : "#cf1322",
                }}
                prefix={<TrophyOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Main Content Area */}
        <Row gutter={[16, 16]}>
          {/* Attendance Table */}
          <Col xs={24} lg={16}>
            <Card
              title={
                <Space>
                  <CalendarOutlined />
                  <span>Attendance History</span>
                </Space>
              }
            >
              <Spin spinning={loading}>
                <Table
                  columns={getAttendanceColumns()}
                  dataSource={attendanceData}
                  rowKey={(record) =>
                    `${record.date}-${record.class_id || "general"}`
                  }
                  pagination={{ pageSize: 10 }}
                  locale={{
                    emptyText: selectedChild
                      ? "No attendance data for this period"
                      : "Please select a child",
                  }}
                />
              </Spin>
            </Card>
          </Col>

          {/* Sidebar */}
          <Col xs={24} lg={8}>
            {/* Attendance Progress */}
            <Card title="Attendance Overview" style={{ marginBottom: "16px" }}>
              <Space direction="vertical" style={{ width: "100%" }}>
                <div>
                  <Text>Present Days</Text>
                  <Progress
                    percent={
                      stats.totalDays > 0
                        ? (stats.presentDays / stats.totalDays) * 100
                        : 0
                    }
                    strokeColor="#52c41a"
                    format={() => `${stats.presentDays}/${stats.totalDays}`}
                  />
                </div>
                <div>
                  <Text>Attendance Rate</Text>
                  <Progress
                    percent={stats.attendanceRate}
                    strokeColor={
                      stats.attendanceRate >= 90
                        ? "#52c41a"
                        : stats.attendanceRate >= 80
                        ? "#faad14"
                        : "#ff4d4f"
                    }
                  />
                </div>
              </Space>
            </Card>

            {/* Recent Alerts */}
            <Card title="Recent Notifications">
              {alerts.length === 0 ? (
                <Text type="secondary">No recent notifications</Text>
              ) : (
                <Timeline size="small">
                  {alerts.map((alert, index) => (
                    <Timeline.Item
                      key={index}
                      color={alert.type === "absence" ? "red" : "blue"}
                      dot={
                        alert.type === "absence" ? (
                          <WarningOutlined />
                        ) : (
                          <MailOutlined />
                        )
                      }
                    >
                      <div>
                        <Text strong>{alert.message}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: "12px" }}>
                          {dayjs(alert.timestamp || alert.created_at).format(
                            "MMM D, YYYY HH:mm",
                          )}
                        </Text>
                      </div>
                    </Timeline.Item>
                  ))}
                </Timeline>
              )}
            </Card>
          </Col>
        </Row>

        {/* Monthly Calendar View */}
        <Row style={{ marginTop: "24px" }}>
          <Col xs={24}>
            <Card title="Monthly Calendar View">
              <Calendar
                dateCellRender={getCalendarDateCellRender}
                headerRender={({ value, onChange }) => (
                  <div
                    style={{
                      padding: "10px 0",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <Title level={4} style={{ margin: 0 }}>
                      {value.format("MMMM YYYY")}
                    </Title>
                    <Space>
                      <Button
                        onClick={() => onChange(value.subtract(1, "month"))}
                      >
                        Previous
                      </Button>
                      <Button type="primary" onClick={() => onChange(dayjs())}>
                        Today
                      </Button>
                      <Button onClick={() => onChange(value.add(1, "month"))}>
                        Next
                      </Button>
                    </Space>
                  </div>
                )}
              />

              {/* Legend */}
              <div style={{ marginTop: "16px", textAlign: "center" }}>
                <Space>
                  <Badge status="success" text="Present (P)" />
                  <Badge status="error" text="Absent (A)" />
                  <Badge status="warning" text="Late (L)" />
                </Space>
              </div>
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default ParentDashboard;
