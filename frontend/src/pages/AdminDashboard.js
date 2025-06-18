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
  Tag,
  Space,
  Typography,
  Alert,
  Spin,
  message,
  Modal,
  Form,
  Input,
  Tabs,
  List,
  Avatar,
} from "antd";
import {
  UserOutlined,
  TeamOutlined,
  BookOutlined,
  BarChartOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  MailOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { useAuth } from "../contexts/AuthContext";
import api from "../services/api";
import dayjs from "dayjs";

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;

const { TabPane } = Tabs;

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  // State for different sections
  const [stats, setStats] = useState({
    totalStudents: 0,
    totalTeachers: 0,
    totalClasses: 0,
    averageAttendance: 0,
    presentToday: 0,
    absentToday: 0,
  });

  const [students, setStudents] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [classes, setClasses] = useState([]);
  const [reports, setReports] = useState([]);
  const [alerts, setAlerts] = useState([]);

  // Modal states
  const [studentModalVisible, setStudentModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);

  // Forms
  const [studentForm] = Form.useForm();

  useEffect(() => {
    fetchOverviewData();
    fetchAlerts();
    fetchReports(); // Charger les rapports dès le début
  }, []);

  useEffect(() => {
    switch (activeTab) {
      case "students":
        fetchStudents();
        break;
      case "teachers":
        fetchTeachers();
        break;
      case "classes":
        fetchClasses();
        break;
      case "reports":
        fetchReports();
        break;
      default:
        // For overview tab, data is already loaded in fetchOverviewData
        break;
    }
  }, [activeTab]);

  const fetchOverviewData = async () => {
    try {
      setLoading(true);

      // Fetch all data for overview
      const [studentsRes, teachersRes, classesRes] = await Promise.all([
        api.get("/students"),
        api.get("/users?role=teacher"),
        api.get("/classes"),
      ]);

      // Get recent reports to find the latest attendance data
      const endDate = dayjs();
      const startDate = endDate.subtract(7, "day");
      const reportsRes = await api.get("/reports/range", {
        params: {
          start_date: startDate.format("YYYY-MM-DD"),
          end_date: endDate.format("YYYY-MM-DD"),
        },
      });

      const studentsData = studentsRes.data || [];
      const teachersData = teachersRes.data?.users || [];
      const classesData = classesRes.data || [];
      const reportsData = reportsRes.data || [];

      // Get the most recent attendance data (latest report)
      let latestAttendance = {
        attendance_rate: 0,
        total_present: 0,
        total_absent: 0,
      };
      if (Array.isArray(reportsData) && reportsData.length > 0) {
        // Reports should be sorted by date, get the most recent one
        latestAttendance = reportsData[0];
      }

      setStats({
        totalStudents: Array.isArray(studentsData) ? studentsData.length : 0,
        totalTeachers: Array.isArray(teachersData) ? teachersData.length : 0,
        totalClasses: Array.isArray(classesData) ? classesData.length : 0,
        averageAttendance: Math.round(latestAttendance.attendance_rate || 0),
        presentToday: latestAttendance.total_present || 0,
        absentToday: latestAttendance.total_absent || 0,
      });
    } catch (error) {
      message.error("Failed to fetch overview data");
      console.error("Error fetching overview data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const response = await api.get("/students");
      setStudents(response.data || []);
    } catch (error) {
      message.error(error.message || "Failed to fetch students");
      console.error("Error fetching students:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeachers = async () => {
    try {
      setLoading(true);
      const response = await api.get("/users?role=teacher");
      setTeachers(response.data?.users || []);
    } catch (error) {
      message.error(error.message || "Failed to fetch teachers");
      console.error("Error fetching teachers:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchClasses = async () => {
    try {
      setLoading(true);
      const response = await api.get("/classes");
      setClasses(response.data || []);
    } catch (error) {
      message.error(error.message || "Failed to fetch classes");
      console.error("Error fetching classes:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReports = async () => {
    try {
      setLoading(true);
      const endDate = dayjs();
      const startDate = endDate.subtract(7, "day");

      const response = await api.get("/reports/range", {
        params: {
          start_date: startDate.format("YYYY-MM-DD"),
          end_date: endDate.format("YYYY-MM-DD"),
        },
      });

      setReports(response.data || []);
    } catch (error) {
      message.error(error.message || "Failed to fetch reports");
      console.error("Error fetching reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await api.get("/alerts");
      // Handle both possible response formats
      const alertsData = Array.isArray(response.data)
        ? response.data
        : response.data?.data || response.data || [];
      setAlerts(alertsData.slice(0, 10)); // Show only recent 10 alerts
    } catch (error) {
      console.error("Error fetching alerts:", error);
      setAlerts([]); // Set empty array on error
    }
  };

  // Student Management
  const handleAddStudent = () => {
    setEditingRecord(null);
    studentForm.resetFields();
    setStudentModalVisible(true);
  };

  const handleEditStudent = (student) => {
    setEditingRecord(student);
    // Properly set form values including nested emergency_contact
    const formValues = {
      ...student,
      emergency_contact: student.emergency_contact || {},
    };
    studentForm.setFieldsValue(formValues);
    setStudentModalVisible(true);
  };

  const handleDeleteStudent = (studentId) => {
    Modal.confirm({
      title: "Delete Student",
      content:
        "Are you sure you want to delete this student? This action cannot be undone.",
      okText: "Delete",
      okType: "danger",
      onOk: async () => {
        try {
          const response = await api.delete(`/students/${studentId}`);
          message.success(response.message || "Student deleted successfully");
          fetchStudents();
        } catch (error) {
          message.error(error.message || "Failed to delete student");
        }
      },
    });
  };

  const handleStudentSubmit = async (values) => {
    try {
      setLoading(true);

      let response;
      if (editingRecord) {
        response = await api.put(`/students/${editingRecord.id}`, values);
        message.success(response.message || "Student updated successfully");
      } else {
        response = await api.post("/students", values);
        message.success(response.message || "Student added successfully");
      }

      setStudentModalVisible(false);
      fetchStudents();
      fetchOverviewData();
    } catch (error) {
      message.error(
        editingRecord ? "Failed to update student" : "Failed to add student",
      );
    } finally {
      setLoading(false);
    }
  };

  // Table columns
  const studentColumns = [
    {
      title: "Name",
      key: "name",
      render: (_, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <span>
            {`${record.first_name || ""} ${record.last_name || ""}`.trim() ||
              "N/A"}
          </span>
        </Space>
      ),
    },
    {
      title: "Student ID",
      dataIndex: "student_id",
      key: "student_id",
      render: (text, record) => text || record?.id || "N/A",
    },
    {
      title: "Grade",
      dataIndex: "grade",
      key: "grade",
      render: (grade) => grade || "N/A",
    },
    {
      title: "Parent Email",
      key: "parent_email",
      render: (_, record) => {
        // Handle different possible field names for parent email
        return (
          record.parent_email ||
          record.emergency_contact?.email ||
          record.parent?.email ||
          "N/A"
        );
      },
    },
    {
      title: "Status",
      key: "status",
      render: () => <Tag color="green">Active</Tag>,
    },
    {
      title: "Actions",
      key: "actions",
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditStudent(record)}
          />
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteStudent(record.id)}
          />
        </Space>
      ),
    },
  ];

  const teacherColumns = [
    {
      title: "Name",
      key: "name",
      render: (_, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <span>
            {`${record.first_name || ""} ${record.last_name || ""}`.trim() ||
              "N/A"}
          </span>
        </Space>
      ),
    },
    {
      title: "Email",
      dataIndex: "email",
      key: "email",
      render: (email) => email || "N/A",
    },
    {
      title: "Role",
      dataIndex: "role",
      key: "role",
      render: (role) => (
        <Tag color="purple">{role?.toUpperCase() || "N/A"}</Tag>
      ),
    },
    {
      title: "Classes",
      key: "classes",
      render: (_, record) => {
        const teacherClasses = (classes || []).filter(
          (cls) => cls.teacher === record.id || cls.teacher === record.email,
        );
        return <Tag color="blue">{teacherClasses.length} Classes</Tag>;
      },
    },
    {
      title: "Status",
      key: "status",
      render: () => <Tag color="green">Active</Tag>,
    },
  ];

  const getOverviewCards = () => (
    <Row gutter={[16, 16]}>
      <Col xs={12} sm={8} md={6}>
        <Card>
          <Statistic
            title="Total Students"
            value={stats.totalStudents}
            prefix={<UserOutlined />}
            valueStyle={{ color: "#1890ff" }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={8} md={6}>
        <Card>
          <Statistic
            title="Total Teachers"
            value={stats.totalTeachers}
            prefix={<TeamOutlined />}
            valueStyle={{ color: "#722ed1" }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={8} md={6}>
        <Card>
          <Statistic
            title="Total Classes"
            value={stats.totalClasses}
            prefix={<BookOutlined />}
            valueStyle={{ color: "#13c2c2" }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={8} md={6}>
        <Card>
          <Statistic
            title="Attendance Rate"
            value={stats.averageAttendance}
            suffix="%"
            prefix={<BarChartOutlined />}
            valueStyle={{
              color:
                stats.averageAttendance >= 80
                  ? "#3f8600"
                  : stats.averageAttendance >= 60
                  ? "#faad14"
                  : "#cf1322",
            }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={8} md={6}>
        <Card>
          <Statistic
            title="Present Today"
            value={stats.presentToday}
            prefix={<CheckCircleOutlined />}
            valueStyle={{ color: "#3f8600" }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={8} md={6}>
        <Card>
          <Statistic
            title="Absent Today"
            value={stats.absentToday}
            prefix={<ExclamationCircleOutlined />}
            valueStyle={{ color: "#cf1322" }}
          />
        </Card>
      </Col>
    </Row>
  );

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
          <TrophyOutlined style={{ fontSize: "24px", color: "#1890ff" }} />
          <Title level={4} style={{ margin: 0 }}>
            Admin Dashboard
          </Title>
        </Space>

        <Space>
          <Text>Welcome, {user?.name}!</Text>
          <Button onClick={logout}>Logout</Button>
        </Space>
      </Header>

      <Content style={{ padding: "24px" }}>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="Overview" key="overview">
            <Spin spinning={loading}>
              {getOverviewCards()}

              {/* Recent Alerts */}
              <Row gutter={[16, 16]} style={{ marginTop: "24px" }}>
                <Col xs={24} lg={16}>
                  <Card
                    title="Recent Reports"
                    extra={<Button onClick={fetchReports}>Refresh</Button>}
                  >
                    {reports.length === 0 ? (
                      <Text type="secondary">No recent reports available</Text>
                    ) : (
                      <List
                        dataSource={reports}
                        renderItem={(report) => (
                          <List.Item>
                            <List.Item.Meta
                              avatar={<Avatar icon={<BarChartOutlined />} />}
                              title={`Daily Report - ${dayjs(
                                report.date,
                              ).format("MMM D, YYYY")}`}
                              description={
                                <Space>
                                  <Tag color="green">
                                    {report.total_present || 0} Present
                                  </Tag>
                                  <Tag color="red">
                                    {report.total_absent || 0} Absent
                                  </Tag>
                                  <Tag color="blue">
                                    {Math.round(report.attendance_rate || 0)}%
                                    Rate
                                  </Tag>
                                </Space>
                              }
                            />
                          </List.Item>
                        )}
                      />
                    )}
                  </Card>
                </Col>

                <Col xs={24} lg={8}>
                  <Card
                    title="Recent Alerts"
                    extra={<Button onClick={fetchAlerts}>Refresh</Button>}
                  >
                    {alerts.length === 0 ? (
                      <Text type="secondary">No recent alerts</Text>
                    ) : (
                      <List
                        dataSource={alerts}
                        renderItem={(alert) => (
                          <List.Item>
                            <List.Item.Meta
                              avatar={
                                <Avatar
                                  icon={
                                    alert.type === "absence" ? (
                                      <WarningOutlined />
                                    ) : (
                                      <MailOutlined />
                                    )
                                  }
                                  style={{
                                    backgroundColor:
                                      alert.type === "absence"
                                        ? "#ff4d4f"
                                        : "#1890ff",
                                  }}
                                />
                              }
                              title={alert.message}
                              description={
                                <Space>
                                  <Tag>{alert.type}</Tag>
                                  <Text
                                    type="secondary"
                                    style={{ fontSize: "12px" }}
                                  >
                                    {dayjs(alert.timestamp).format(
                                      "MMM D, HH:mm",
                                    )}
                                  </Text>
                                </Space>
                              }
                            />
                          </List.Item>
                        )}
                      />
                    )}
                  </Card>
                </Col>
              </Row>
            </Spin>
          </TabPane>

          <TabPane tab="Students" key="students">
            <Card
              title={`Student Management (${students.length})`}
              extra={
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAddStudent}
                >
                  Add Student
                </Button>
              }
            >
              {students.length === 0 && !loading ? (
                <Alert
                  message="No students found"
                  description="No students have been added yet. Click 'Add Student' to get started."
                  type="info"
                  showIcon
                />
              ) : (
                <Table
                  columns={studentColumns}
                  dataSource={students}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 10 }}
                />
              )}
            </Card>
          </TabPane>

          <TabPane tab="Teachers" key="teachers">
            <Card title={`Teacher Management (${teachers.length})`}>
              {teachers.length === 0 && !loading ? (
                <Alert
                  message="No teachers found"
                  description="No teachers have been registered yet."
                  type="info"
                  showIcon
                />
              ) : (
                <Table
                  columns={teacherColumns}
                  dataSource={teachers}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 10 }}
                />
              )}
            </Card>
          </TabPane>

          <TabPane tab="Classes" key="classes">
            <Card title={`Class Management (${classes.length})`}>
              {classes.length === 0 && !loading ? (
                <Alert
                  message="No classes found"
                  description="No classes have been created yet."
                  type="info"
                  showIcon
                />
              ) : (
                <Table
                  columns={[
                    {
                      title: "Class ID",
                      dataIndex: "id",
                      key: "id",
                      render: (text) => text || "N/A",
                    },
                    {
                      title: "Name",
                      dataIndex: "name",
                      key: "name",
                      render: (text) => text || "N/A",
                    },
                    {
                      title: "Teacher",
                      dataIndex: "teacher_id",
                      key: "teacher_id",
                      render: (teacherId) => {
                        const teacher = teachers.find(
                          (t) => t.id === teacherId || t.email === teacherId,
                        );
                        if (teacher) {
                          return (
                            `${teacher.first_name || ""} ${
                              teacher.last_name || ""
                            }`.trim() ||
                            teacher.email ||
                            "N/A"
                          );
                        }
                        return teacherId || "N/A";
                      },
                    },
                    {
                      title: "Students",
                      key: "students",
                      render: (_, record) => (
                        <Tag color="blue">
                          {(record.students || []).length} Students
                        </Tag>
                      ),
                    },
                  ]}
                  dataSource={classes}
                  rowKey="id"
                  loading={loading}
                  pagination={{ pageSize: 10 }}
                />
              )}
            </Card>
          </TabPane>
        </Tabs>

        {/* Student Modal */}
        <Modal
          title={editingRecord ? "Edit Student" : "Add Student"}
          open={studentModalVisible}
          onOk={() => studentForm.submit()}
          onCancel={() => setStudentModalVisible(false)}
          confirmLoading={loading}
        >
          <Form
            form={studentForm}
            onFinish={handleStudentSubmit}
            layout="vertical"
          >
            <Form.Item
              name="first_name"
              label="First Name"
              rules={[{ required: true }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="last_name"
              label="Last Name"
              rules={[{ required: true }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="student_id"
              label="Student ID"
              rules={[{ required: true }]}
            >
              <Input placeholder="e.g., AA2024001" />
            </Form.Item>
            <Form.Item name="grade" label="Grade" rules={[{ required: true }]}>
              <Select>
                {["9A", "9B", "10A", "10B", "11A", "11B", "12A", "12B"].map(
                  (grade) => (
                    <Option key={grade} value={grade}>
                      {grade}
                    </Option>
                  ),
                )}
              </Select>
            </Form.Item>
            <Form.Item
              name={["emergency_contact", "email"]}
              label="Parent/Guardian Email"
              rules={[{ required: true, type: "email" }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name={["emergency_contact", "name"]}
              label="Parent/Guardian Name"
              rules={[{ required: true }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name={["emergency_contact", "phone"]}
              label="Emergency Contact Phone"
            >
              <Input />
            </Form.Item>
          </Form>
        </Modal>
      </Content>
    </Layout>
  );
};

export default AdminDashboard;
