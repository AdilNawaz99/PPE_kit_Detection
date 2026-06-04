import React, { useState, useEffect, useCallback } from 'react';
import io from 'socket.io-client';
import axios from 'axios';
import { Container, Row, Col, Card, Button, Form, Alert, Badge, Table } from 'react-bootstrap';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './App.css';

const BACKEND_URL = 'http://localhost:5000';

function App() {
  const [cameras, setCameras] = useState([]);
  const [newCameraId, setNewCameraId] = useState('');
  const [newCameraSource, setNewCameraSource] = useState('0');
  const [stats, setStats] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [violationEvents, setViolationEvents] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [lastSyncTime, setLastSyncTime] = useState(null);

  // Fetch cameras list
  const fetchCameras = useCallback(async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/cameras`);
      setCameras(response.data.cameras);
      if (response.data.cameras.length > 0) {
        setSelectedCamera((prev) => prev || response.data.cameras[0]);
      }

      // Auto-connect default webcam for a quick start experience.
      if (response.data.cameras.length === 0) {
        await axios.post(`${BACKEND_URL}/cameras`, {
          camera_id: 'Webcam-0',
          source: 0
        });
        const refreshed = await axios.get(`${BACKEND_URL}/cameras`);
        setCameras(refreshed.data.cameras);
        if (refreshed.data.cameras.length > 0) {
          setSelectedCamera((prev) => prev || refreshed.data.cameras[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching cameras:', error);
    }
  }, []);

  // Initialize Socket.IO connection
  useEffect(() => {
    const newSocket = io(BACKEND_URL, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    newSocket.on('connect', () => {
      console.log('Connected to backend');
    });

    newSocket.on('alert', (data) => {
      setAlerts((prev) => [data, ...prev.slice(0, 19)]);
    });

    newSocket.on('violation_event', (data) => {
      setViolationEvents((prev) => [data, ...prev.slice(0, 29)]);
    });

    newSocket.on('camera_added', () => {
      fetchCameras();
    });

    newSocket.on('camera_removed', () => {
      fetchCameras();
    });

    return () => newSocket.close();
  }, [fetchCameras]);

  // Fetch statistics
  useEffect(() => {
    const syncStats = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/stats`);
        setStats(response.data);

        const allAlerts = Object.entries(response.data)
          .flatMap(([cameraId, data]) =>
            (data.recent_alerts || []).map((alert) => ({
              ...alert,
              camera_id: alert.camera_id || cameraId
            }))
          )
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        const allViolations = Object.entries(response.data)
          .flatMap(([cameraId, data]) =>
            (data.recent_violations || []).map((event) => ({
              ...event,
              camera_id: event.camera_id || cameraId
            }))
          )
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        setAlerts(allAlerts.slice(0, 20));
        setViolationEvents(allViolations.slice(0, 30));
        setLastSyncTime(new Date().toISOString());
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    syncStats();
    const interval = setInterval(syncStats, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  // Fetch cameras on mount
  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  // Add new camera
  const handleAddCamera = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${BACKEND_URL}/cameras`, {
        camera_id: newCameraId,
        source: newCameraSource
      });
      if (response.status === 201) {
        setNewCameraId('');
        setNewCameraSource('0');
        fetchCameras();
      }
    } catch (error) {
      alert('Error adding camera: ' + (error.response?.data?.error || error.message));
    }
  };

  // Remove camera
  const handleRemoveCamera = async (cameraId) => {
    try {
      await axios.delete(`${BACKEND_URL}/cameras/${cameraId}`);
      fetchCameras();
      if (selectedCamera === cameraId) {
        setSelectedCamera(cameras[0] || null);
      }
    } catch (error) {
      alert('Error removing camera: ' + error.message);
    }
  };

  const currentStats = selectedCamera && stats[selectedCamera];
  const shownViolations = selectedCamera
    ? violationEvents.filter(event => event.camera_id === selectedCamera)
    : violationEvents;

  return (
    <div className="app">
      <header className="header">
        <Container>
          <h1>🚨 PPE Detection Dashboard</h1>
          <p>Real-time Construction Site Safety Monitoring</p>
        </Container>
      </header>

      <Container fluid className="body">
        {/* Add Camera Section */}
        <Row className="mb-4">
          <Col md={8}>
            <Card>
              <Card.Body>
                <Card.Title>Add Camera</Card.Title>
                <Form onSubmit={handleAddCamera}>
                  <Row>
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label>Camera ID</Form.Label>
                        <Form.Control
                          type="text"
                          placeholder="e.g., Camera-1"
                          value={newCameraId}
                          onChange={(e) => setNewCameraId(e.target.value)}
                          required
                        />
                      </Form.Group>
                    </Col>
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label>Source</Form.Label>
                        <Form.Control
                          type="text"
                          placeholder="0 for webcam or file path"
                          value={newCameraSource}
                          onChange={(e) => setNewCameraSource(e.target.value)}
                          required
                        />
                        <Form.Text className="text-muted">
                          Use 0 for webcam, or path to video file
                        </Form.Text>
                      </Form.Group>
                    </Col>
                    <Col md={4} className="d-flex align-items-end">
                      <Button variant="success" type="submit" className="w-100">
                        Add Camera
                      </Button>
                    </Col>
                  </Row>
                </Form>
              </Card.Body>
            </Card>
          </Col>

          <Col md={4}>
            <Card className="bg-info text-white">
              <Card.Body>
                <Card.Title>Active Cameras</Card.Title>
                <h3>{cameras.length}</h3>
                <small>Monitoring in real-time</small>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Camera Selection and Live Feed */}
        <Row className="mb-4">
          <Col md={9}>
            <Card>
              <Card.Body>
                <Card.Title>Live Feed</Card.Title>
                {selectedCamera ? (
                  <div className="feed-container">
                    <img
                      src={`${BACKEND_URL}/video_feed/${selectedCamera}`}
                      alt={`Camera: ${selectedCamera}`}
                      className="feed-image"
                    />
                  </div>
                ) : (
                  <Alert variant="warning">No cameras connected</Alert>
                )}
              </Card.Body>
            </Card>
          </Col>

          <Col md={3}>
            <Card>
              <Card.Body>
                <Card.Title>Cameras</Card.Title>
                {cameras.length > 0 ? (
                  <div className="camera-list">
                    {cameras.map(cam => (
                      <div key={cam} className="camera-item mb-2">
                        <Button
                          variant={selectedCamera === cam ? 'primary' : 'outline-primary'}
                          size="sm"
                          onClick={() => setSelectedCamera(cam)}
                          className="w-75"
                        >
                          {cam}
                        </Button>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => handleRemoveCamera(cam)}
                          className="w-25 ms-1"
                        >
                          ✕
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No cameras yet</p>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Statistics */}
        {currentStats && (
          <Row className="mb-4">
            <Col md={3}>
              <Card className="stat-card">
                <Card.Body className="text-center">
                  <h6>Total Detections</h6>
                  <h2>{currentStats.total_detections}</h2>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="stat-card">
                <Card.Body className="text-center">
                  <h6>Safe Items</h6>
                  <h2>{currentStats.detections_by_class?.Hardhat || 0}</h2>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="stat-card bg-warning">
                <Card.Body className="text-center">
                  <h6>Missing PPE</h6>
                  <h2>
                    {(currentStats.detections_by_class?.['NO-Hardhat'] || 0) +
                      (currentStats.detections_by_class?.['NO-Mask'] || 0) +
                      (currentStats.detections_by_class?.['NO-Safety Vest'] || 0)}
                  </h2>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="stat-card">
                <Card.Body className="text-center">
                  <h6>Last Update</h6>
                  <small>
                    {currentStats.last_updated
                      ? new Date(currentStats.last_updated).toLocaleTimeString()
                      : 'N/A'}
                  </small>
                  <div className="mt-1">
                    <Badge bg={currentStats.camera_status === 'live' ? 'success' : 'secondary'}>
                      {currentStats.camera_status === 'live' ? 'LIVE' : 'WAITING FOR CAMERA'}
                    </Badge>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {/* Detection Breakdown Chart */}
        {currentStats && (
          <Row className="mb-4">
            <Col md={6}>
              <Card>
                <Card.Body>
                  <Card.Title>Detection Breakdown</Card.Title>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={Object.entries(currentStats.detections_by_class || {}).map(([name, value]) => ({
                          name,
                          value
                        }))}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#FF6B6B', '#4ECDC4'].map((color, idx) => (
                          <Cell key={`cell-${idx}`} fill={color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Card.Body>
              </Card>
            </Col>

            <Col md={6}>
              <Card>
                <Card.Body>
                  <Card.Title>Detection Classes</Card.Title>
                  <Table striped bordered hover size="sm">
                    <tbody>
                      {Object.entries(currentStats.detections_by_class || {})
                        .sort(([, a], [, b]) => b - a)
                        .map(([className, count]) => (
                          <tr key={className}>
                            <td>{className}</td>
                            <td>
                              <Badge bg={className.includes('NO-') ? 'danger' : 'success'}>
                                {count}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        )}

        {/* Alerts */}
        <Row>
          <Col>
            <Card className="alerts-card">
              <Card.Body>
                <Card.Title>Recent Alerts (Safety Violations)</Card.Title>
                <small className="text-muted d-block mb-2">
                  Auto-refresh every 5 seconds. Last sync: {lastSyncTime ? new Date(lastSyncTime).toLocaleTimeString() : 'N/A'}
                </small>
                {alerts.length > 0 ? (
                  <div className="alerts-list" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {alerts.map((alert, idx) => (
                      <Alert key={idx} variant="danger" className="mb-2">
                        <strong>{alert.class}</strong> at {alert.camera_id}
                        <br />
                        <span>{alert.description || 'Safety violation detected from live stream.'}</span>
                        <br />
                        <small className="text-muted">
                          {new Date(alert.timestamp).toLocaleString()}
                        </small>
                      </Alert>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No recent alerts in the last captured cycle. Camera is monitoring in real time.</p>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Violation Captures */}
        <Row className="mt-4">
          <Col>
            <Card className="alerts-card">
              <Card.Body>
                <Card.Title>Violation Captures (Every 5 Seconds)</Card.Title>
                <small className="text-muted d-block mb-2">
                  Snapshot cards appear whenever NO-Mask / NO-Safety Vest / NO-Hardhat is detected.
                </small>
                {shownViolations.length > 0 ? (
                  <div className="violation-grid">
                    {shownViolations.slice(0, 12).map((event, idx) => (
                      <Card key={`${event.timestamp}-${idx}`} className="violation-card">
                        <Card.Img
                          variant="top"
                          src={`${BACKEND_URL}${event.image_url}`}
                          alt={`Violation at ${event.camera_id}`}
                        />
                        <Card.Body>
                          <div className="mb-2">
                            {event.violation_types?.map((violation) => (
                              <Badge bg="danger" className="me-1" key={violation}>
                                {violation}
                              </Badge>
                            ))}
                          </div>
                          <small className="text-muted">
                            {event.camera_id} - {new Date(event.timestamp).toLocaleString()}
                          </small>
                          <div className="mt-1 small">
                            {event.description || 'Violation snapshot captured from live feed.'}
                          </div>
                        </Card.Body>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted">No violation snapshots yet. This section updates every 5 seconds when a violation appears.</p>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default App;
