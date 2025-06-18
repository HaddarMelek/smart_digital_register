import React, { useState, useEffect } from "react";
import {
  Form,
  Input,
  Button,
  Card,
  Typography,
  Alert,
  Row,
  Col,
  Space,
} from "antd";
import { UserOutlined, LockOutlined, BookOutlined } from "@ant-design/icons";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate, useLocation } from "react-router-dom";

const { Title, Paragraph } = Typography;

const Login = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      const from =
        location.state?.from?.pathname || getDashboardRoute(user.role);
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, user, navigate, location]);

  const getDashboardRoute = (role) => {
    switch (role) {
      case "teacher":
        return "/teacher";
      case "admin":
        return "/admin";
      case "parent":
        return "/parent";
      default:
        return "/";
    }
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    setError("");

    try {
      const result = await login(values.email, values.password);

      if (result.success) {
        const from =
          location.state?.from?.pathname || getDashboardRoute(result.user.role);
        navigate(from, { replace: true });
      } else {
        setError(result.error || "Login failed. Please try again.");
      }
    } catch (err) {
      setError("An unexpected error occurred. Please try again.");
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      <Row
        gutter={[32, 32]}
        align="middle"
        style={{ width: "100%", maxWidth: "1200px" }}
      >
        {/* Welcome Section */}
        <Col xs={24} lg={12}>
          <div
            style={{ color: "white", textAlign: { xs: "center", lg: "left" } }}
          >
            <Space align="center" size="large" style={{ marginBottom: "2rem" }}>
              <BookOutlined style={{ fontSize: "3rem" }} />
              <Title level={1} style={{ color: "white", margin: 0 }}>
                Alexander Academy
              </Title>
            </Space>

            <Title level={2} style={{ color: "white", fontWeight: 300 }}>
              Intelligent Attendance Register
            </Title>

            <Paragraph
              style={{
                color: "rgba(255,255,255,0.8)",
                fontSize: "1.1rem",
                lineHeight: 1.6,
              }}
            >
              Welcome to our advanced attendance management system. Track
              student attendance, receive AI-powered insights, and stay
              connected with automated reports and alerts.
            </Paragraph>

            <div style={{ marginTop: "2rem" }}>
              <Space direction="vertical" size="small">
                <div style={{ color: "rgba(255,255,255,0.9)" }}>
                  ✓ Manual attendance marking by teachers
                </div>
                <div style={{ color: "rgba(255,255,255,0.9)" }}>
                  ✓ AI-powered absence predictions
                </div>
                <div style={{ color: "rgba(255,255,255,0.9)" }}>
                  ✓ Automated parent notifications
                </div>
                <div style={{ color: "rgba(255,255,255,0.9)" }}>
                  ✓ Comprehensive attendance reports
                </div>
              </Space>
            </div>
          </div>
        </Col>

        {/* Login Form */}
        <Col xs={24} lg={12}>
          <Card
            style={{
              maxWidth: "400px",
              margin: "0 auto",
              boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
              borderRadius: "12px",
            }}
          >
            <div style={{ textAlign: "center", marginBottom: "2rem" }}>
              <Title level={3} style={{ marginBottom: "0.5rem" }}>
                Welcome Back
              </Title>
              <Paragraph type="secondary">
                Sign in to your account to continue
              </Paragraph>
            </div>

            {error && (
              <Alert
                message={error}
                type="error"
                showIcon
                style={{ marginBottom: "1rem" }}
              />
            )}

            <Form
              form={form}
              name="login"
              onFinish={handleSubmit}
              layout="vertical"
              size="large"
              requiredMark={false}
            >
              <Form.Item
                name="email"
                label="Email Address"
                rules={[
                  {
                    required: true,
                    message: "Please enter your email address",
                  },
                  {
                    type: "email",
                    message: "Please enter a valid email address",
                  },
                ]}
              >
                <Input
                  prefix={<UserOutlined />}
                  placeholder="Enter your email"
                  autoComplete="email"
                />
              </Form.Item>

              <Form.Item
                name="password"
                label="Password"
                rules={[
                  { required: true, message: "Please enter your password" },
                  { min: 6, message: "Password must be at least 6 characters" },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined />}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                />
              </Form.Item>

              <Form.Item style={{ marginBottom: "1rem" }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  style={{
                    width: "100%",
                    height: "48px",
                    fontSize: "16px",
                    borderRadius: "6px",
                  }}
                >
                  {loading ? "Signing In..." : "Sign In"}
                </Button>
              </Form.Item>
            </Form>

            <div style={{ textAlign: "center", marginTop: "1rem" }}>
              <Paragraph type="secondary" style={{ fontSize: "14px" }}>
                Having trouble signing in? Contact your system administrator.
              </Paragraph>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Login;
