import React, { useState, useEffect, useCallback } from "react";
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
  Modal,
  Form,
  Radio,
  Tooltip,
  Badge,
} from "antd";
import {
  UserOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  PlusOutlined,
  BookOutlined,
  BulbOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";
import dayjs from "dayjs";

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;

const TeacherDashboard = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [students, setStudents] = useState([]);
  const [attendanceDate, setAttendanceDate] = useState(dayjs());
  const [attendanceData, setAttendanceData] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [stats, setStats] = useState({
    totalStudents: 0,
    presentToday: 0,
    absentToday: 0,
    attendanceRate: 0,
  });
  const [markAttendanceVisible, setMarkAttendanceVisible] = useState(false);
  const [markingForm] = Form.useForm();

  // Fetch teacher's classes on component mount
  useEffect(() => {
    fetchClasses();
  }, []);

  // Fetch students and attendance when class or date changes
  useEffect(() => {
    if (selectedClass) {
      fetchStudents();
      fetchAttendance();
      fetchPredictions();
    }
  }, [selectedClass, attendanceDate]);

  // Re-fetch attendance when students are loaded
  useEffect(() => {
    if (selectedClass && students.length > 0 && attendanceData.length === 0) {
      fetchAttendance();
    }
  }, [students]);

  const fetchClasses = async () => {
    try {
      setLoading(true);
      const response = await api.get("/classes");

      // Try both possible response formats
      const allClasses = Array.isArray(response.data)
        ? response.data
        : response.data?.classes || response.data || [];

      const teacherClasses = allClasses.filter(
        (cls) => cls.teacher_id === user.id || cls.teacher === user.id,
      );

      setClasses(teacherClasses);

      if (teacherClasses.length > 0) {
        setSelectedClass(teacherClasses[0].id);
      }
    } catch (error) {
      message.error(error.message || "Failed to fetch classes");
      console.error("Error fetching classes:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudents = async () => {
    if (!selectedClass) return;

    try {
      const response = await api.get(`/classes/${selectedClass}/students`);

      // Try both possible response formats
      const studentsData = Array.isArray(response.data)
        ? response.data
        : response.data?.students || response.data || [];

      setStudents(studentsData);

      // Update total students stat
      setStats((prev) => ({
        ...prev,
        totalStudents: studentsData.length,
      }));
    } catch (error) {
      message.error(error.message || "Failed to fetch students");
      console.error("Error fetching students:", error);
    }
  };

  const fetchAttendance = async () => {
    if (!selectedClass) return;

    try {
      const dateStr = attendanceDate.format("YYYY-MM-DD");
      const response = await api.get(
        `/attendance/class/${selectedClass}/date/${dateStr}`,
      );

      // Handle different response formats
      let attendance = [];

      if (Array.isArray(response.data)) {
        attendance = response.data;
      } else if (response.data?.data?.attendance) {
        // New format from POST attendance response
        attendance = response.data.data.attendance;
      } else if (response.data?.attendance) {
        attendance = response.data.attendance;
      } else {
        attendance = response.data || [];
      }

      // Store raw attendance data temporarily
      const rawAttendanceData = attendance;

      // If we don't have students data yet, fetch it first
      if (students.length === 0) {
        // We'll need to call fetchStudents and then recall this function
        // For now, just set empty combined data and let the next cycle handle it
        setAttendanceData([]);
        return;
      }

      // Combine with student data
      const combinedData = students.map((student) => {
        const attendanceRecord = rawAttendanceData.find((att) => {
          // Handle both old and new response formats
          const studentId = att.student_id || att.attendance?.student_id;
          return studentId === student.id;
        });

        // Extract attendance info from either format
        let status = "absent";
        let marked_at = null;
        let notes = "";

        if (attendanceRecord) {
          if (attendanceRecord.attendance) {
            // New format: {attendance: {...}, student: {...}}
            status =
              attendanceRecord.attendance.status ||
              attendanceRecord.status ||
              "absent";
            marked_at =
              attendanceRecord.attendance.marked_at ||
              attendanceRecord.marked_at;
            notes =
              attendanceRecord.attendance.notes || attendanceRecord.notes || "";
          } else {
            // Old format: direct fields
            status = attendanceRecord.status || "absent";
            marked_at = attendanceRecord.marked_at;
            notes = attendanceRecord.notes || "";
          }
        }

        return {
          student_id: student.id,
          student_name:
            `${student.first_name || ""} ${student.last_name || ""}`.trim() ||
            student.name ||
            `Student ${student.student_id || student.id}`,
          status: status,
          marked_at: marked_at,
          notes: notes,
        };
      });

      setAttendanceData(combinedData);

      // Calculate stats
      const presentCount = combinedData.filter(
        (a) => a.status === "present",
      ).length;
      const absentCount = combinedData.filter(
        (a) => a.status === "absent",
      ).length;
      const rate =
        combinedData.length > 0
          ? (presentCount / combinedData.length) * 100
          : 0;

      setStats((prev) => ({
        ...prev,
        presentToday: presentCount,
        absentToday: absentCount,
        attendanceRate: Math.round(rate),
      }));
    } catch (error) {
      message.error(error.message || "Failed to fetch attendance data");
      console.error("Error fetching attendance:", error);
    }
  };

  const fetchPredictions = async () => {
    if (!selectedClass) return;

    try {
      const response = await api.get(`/predictions/class/${selectedClass}`);

      // The response should have data.predictions format based on the backend
      const predictions =
        response.data?.data?.predictions || response.data?.predictions || [];
      setPredictions(predictions);
    } catch (error) {
      console.error("Error fetching predictions:", error);
      // Don't show error message as predictions are optional
    }
  };

  const handleMarkAttendance = () => {
    markingForm.resetFields();
    setMarkAttendanceVisible(true);

    // Pre-populate form with current attendance or default to present
    const initialValues = students.reduce((acc, student) => {
      const existingAttendance = attendanceData.find(
        (a) => a.student_id === student.id,
      );
      acc[student.id] = existingAttendance?.status || "present";
      return acc;
    }, {});

    markingForm.setFieldsValue(initialValues);
  };

  const submitAttendance = async (values) => {
    try {
      setLoading(true);

      const attendanceRecords = Object.entries(values).map(
        ([studentId, status]) => ({
          student_id: studentId,
          status,
          notes: "", // Could be extended to include notes
        }),
      );

      const response = await api.post("/attendance", {
        class_id: selectedClass,
        date: attendanceDate.format("YYYY-MM-DD"),
        attendance: attendanceRecords,
      });

      message.success(response.message || "Attendance marked successfully");
      setMarkAttendanceVisible(false);
      fetchAttendance(); // Refresh attendance data
    } catch (error) {
      message.error(error.message || "Failed to mark attendance");
      console.error("Error marking attendance:", error);
    } finally {
      setLoading(false);
    }
  };

  const getAttendanceColumns = () => [
    {
      title: "Student",
      dataIndex: "student_name",
      key: "student_name",
      render: (name, record) => (
        <Space>
          <UserOutlined />
          <span>{name || `Student ${record.student_id}`}</span>
        </Space>
      ),
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (status) => {
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
          late: { color: "orange", icon: <CalendarOutlined />, text: "Late" },
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
      title: "Time Marked",
      dataIndex: "marked_at",
      key: "marked_at",
      render: (time) => (time ? dayjs(time).format("HH:mm:ss") : "-"),
    },
    {
      title: "AI Prediction",
      key: "prediction",
      render: (_, record) => {
        const prediction = predictions.find(
          (p) => p.student_id === record.student_id,
        );
        if (!prediction) return "-";

        const riskLevel = prediction.risk_level;
        const attendanceRate = prediction.attendance_rate;

        const riskConfig = {
          high: { color: "red", text: "High Risk" },
          medium: { color: "orange", text: "Medium Risk" },
          low: { color: "green", text: "Low Risk" },
        };

        const config = riskConfig[riskLevel] || riskConfig.low;

        return (
          <Tooltip
            title={`${attendanceRate}% attendance rate - ${prediction.recommendation}`}
          >
            <Badge color={config.color} text={config.text} />
          </Tooltip>
        );
      },
    },
  ];

  const selectedClassName =
    classes.find((c) => c.id === selectedClass)?.name || "Select Class";

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
          <BookOutlined style={{ fontSize: "24px", color: "#1890ff" }} />
          <Title level={4} style={{ margin: 0 }}>
            Teacher Dashboard
          </Title>
        </Space>

        <Space>
          <Text>Welcome, {user?.name}!</Text>
          <Button onClick={logout}>Logout</Button>
        </Space>
      </Header>

      <Content style={{ padding: "24px" }}>
        {/* Class and Date Selection */}
        <Row gutter={[16, 16]} style={{ marginBottom: "24px" }}>
          <Col xs={24} sm={12} md={8}>
            <Card size="small">
              <Space direction="vertical" style={{ width: "100%" }}>
                <Text strong>Select Class:</Text>
                <Select
                  style={{ width: "100%" }}
                  value={selectedClass}
                  onChange={setSelectedClass}
                  placeholder="Choose a class"
                >
                  {classes.map((cls) => (
                    <Option key={cls.id} value={cls.id}>
                      {cls.name} - {cls.subject}
                    </Option>
                  ))}
                </Select>
              </Space>
            </Card>
          </Col>

          <Col xs={24} sm={12} md={8}>
            <Card size="small">
              <Space direction="vertical" style={{ width: "100%" }}>
                <Text strong>Select Date:</Text>
                <DatePicker
                  style={{ width: "100%" }}
                  value={attendanceDate}
                  onChange={setAttendanceDate}
                  disabledDate={(date) => date.isAfter(dayjs())}
                />
              </Space>
            </Card>
          </Col>

          <Col xs={24} sm={24} md={8}>
            <Card size="small">
              <Space style={{ width: "100%", justifyContent: "space-between" }}>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleMarkAttendance}
                  disabled={!selectedClass || !students.length}
                >
                  Mark Attendance
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={fetchAttendance}
                  disabled={!selectedClass}
                >
                  Refresh
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* Statistics */}
        <Row gutter={[16, 16]} style={{ marginBottom: "24px" }}>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="Total Students"
                value={stats.totalStudents}
                prefix={<UserOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="Present Today"
                value={stats.presentToday}
                valueStyle={{ color: "#3f8600" }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="Absent Today"
                value={stats.absentToday}
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
                    stats.attendanceRate >= 80
                      ? "#3f8600"
                      : stats.attendanceRate >= 60
                      ? "#faad14"
                      : "#cf1322",
                }}
              />
            </Card>
          </Col>
        </Row>

        {/* AI Predictions Alert */}
        {predictions.length > 0 && (
          <Alert
            message="AI Insights Available"
            description={
              <Space direction="vertical" size="small">
                <Text>
                  Our AI has analyzed attendance patterns and identified
                  students at risk of absence.
                </Text>
                <Text type="secondary">
                  <BulbOutlined /> Check the "AI Prediction" column in the
                  attendance table below.
                </Text>
              </Space>
            }
            type="info"
            icon={<BulbOutlined />}
            showIcon
            style={{ marginBottom: "24px" }}
          />
        )}

        {/* Attendance Table */}
        <Card
          title={
            <Space>
              <CalendarOutlined />
              <span>
                Attendance for {selectedClassName} -{" "}
                {attendanceDate.format("MMMM D, YYYY")}
              </span>
            </Space>
          }
        >
          <Spin spinning={loading}>
            <Table
              columns={getAttendanceColumns()}
              dataSource={attendanceData}
              rowKey="student_id"
              pagination={false}
              locale={{
                emptyText: selectedClass
                  ? "No attendance data for this date"
                  : "Please select a class",
              }}
            />
          </Spin>
        </Card>

        {/* Mark Attendance Modal */}
        <Modal
          title="Mark Attendance"
          open={markAttendanceVisible}
          onOk={() => markingForm.submit()}
          onCancel={() => setMarkAttendanceVisible(false)}
          width={600}
          confirmLoading={loading}
        >
          <Form
            form={markingForm}
            onFinish={submitAttendance}
            layout="vertical"
          >
            <Text
              type="secondary"
              style={{ display: "block", marginBottom: "16px" }}
            >
              Mark attendance for {selectedClassName} on{" "}
              {attendanceDate.format("MMMM D, YYYY")}
            </Text>

            {students.map((student) => (
              <Form.Item
                key={student.id}
                name={student.id}
                label={`${student.first_name} ${student.last_name}`}
                initialValue="present"
              >
                <Radio.Group>
                  <Radio value="present">
                    <Tag color="green" icon={<CheckCircleOutlined />}>
                      Present
                    </Tag>
                  </Radio>
                  <Radio value="absent">
                    <Tag color="red" icon={<ExclamationCircleOutlined />}>
                      Absent
                    </Tag>
                  </Radio>
                  <Radio value="late">
                    <Tag color="orange" icon={<CalendarOutlined />}>
                      Late
                    </Tag>
                  </Radio>
                </Radio.Group>
              </Form.Item>
            ))}
          </Form>
        </Modal>
      </Content>
    </Layout>
  );
};

export default TeacherDashboard;
