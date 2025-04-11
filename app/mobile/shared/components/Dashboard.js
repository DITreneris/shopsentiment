/**
 * Dashboard Component
 * Main dashboard screen for the Shop Sentiment mobile app
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Image,
  SafeAreaView,
  StatusBar,
  Dimensions,
} from 'react-native';
import { LineChart, BarChart } from 'react-native-chart-kit';
import apiClient from '../api_client';
import dataSyncService from '../data_sync';
import notificationManager from '../notification_manager';
import config from '../config';

const { width } = Dimensions.get('window');

const Dashboard = ({ navigation }) => {
  // State variables
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [error, setError] = useState(null);
  const [isOnline, setIsOnline] = useState(true);

  // Fetch dashboard data on component mount
  useEffect(() => {
    fetchDashboardData();
    
    // Subscribe to network state changes
    const unsubscribe = dataSyncService.addSyncListener(handleSyncEvent);
    
    // Initialize notification manager
    notificationManager.initialize();
    
    return () => {
      unsubscribe();
    };
  }, []);

  // Handle data sync events
  const handleSyncEvent = (event) => {
    if (event.type === 'networkChange') {
      setIsOnline(event.isOnline);
    } else if (event.type === 'syncCompleted') {
      // Refresh data after sync completion
      fetchDashboardData();
    }
  };

  // Fetch dashboard data from API
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Example data structure - in real app, would come from API
      const data = {
        recentRecommendations: [
          { id: '1', name: 'Product A', category: 'Electronics', score: 0.92 },
          { id: '2', name: 'Product B', category: 'Clothing', score: 0.89 },
          { id: '3', name: 'Product C', category: 'Home', score: 0.85 },
        ],
        sentimentTrend: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
          datasets: [
            {
              data: [4.1, 4.3, 4.0, 4.2, 4.5, 4.6],
              color: () => config.app.theme.primaryColor,
              strokeWidth: 2,
            },
          ],
        },
        categoryPerformance: {
          labels: ['Electronics', 'Clothing', 'Home', 'Beauty', 'Books'],
          data: [0.8, 0.6, 0.7, 0.9, 0.5],
        },
        alerts: [
          { id: '1', title: 'Price Drop Alert', message: 'Product A price dropped by 15%', type: 'price' },
          { id: '2', title: 'Trending Product', message: 'Product B is trending in your category', type: 'trend' },
        ],
      };
      
      // Cache the dashboard data
      setDashboardData(data);
      
      // Schedule a notification for the first alert
      if (data.alerts && data.alerts.length > 0) {
        notificationManager.scheduleNotification({
          title: data.alerts[0].title,
          message: data.alerts[0].message,
          channelId: data.alerts[0].type === 'price' ? 'price_alerts' : 'recommendations',
          date: new Date(Date.now() + 5000), // 5 seconds from now (for demo)
        });
      }
      
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Pull down to refresh.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Handle pull-to-refresh
  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  // Render loading state
  if (loading && !refreshing && !dashboardData) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={config.app.theme.primaryColor} />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar backgroundColor={config.app.theme.primaryColor} barStyle="light-content" />
      
      {/* Dashboard Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Shop Sentiment</Text>
        {!isOnline && (
          <View style={styles.offlineBadge}>
            <Text style={styles.offlineText}>Offline</Text>
          </View>
        )}
      </View>
      
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Error Message */}
        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
        
        {/* Recent Recommendations */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Recommendations</Text>
          <View style={styles.recommendationsContainer}>
            {dashboardData?.recentRecommendations.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={styles.recommendationItem}
                onPress={() => navigation.navigate('ProductDetails', { productId: item.id })}
              >
                <View style={styles.recommendationContent}>
                  <Image
                    source={{ uri: `https://via.placeholder.com/50?text=${item.name.charAt(0)}` }}
                    style={styles.productImage}
                  />
                  <View style={styles.productInfo}>
                    <Text style={styles.productName}>{item.name}</Text>
                    <Text style={styles.productCategory}>{item.category}</Text>
                  </View>
                </View>
                <View style={styles.scoreContainer}>
                  <Text style={styles.scoreText}>{(item.score * 100).toFixed(0)}%</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>
          <TouchableOpacity 
            style={styles.viewAllButton}
            onPress={() => navigation.navigate('Recommendations')}
          >
            <Text style={styles.viewAllText}>View All Recommendations</Text>
          </TouchableOpacity>
        </View>
        
        {/* Sentiment Trend Chart */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Sentiment Trend</Text>
          <View style={styles.chartContainer}>
            <LineChart
              data={dashboardData?.sentimentTrend}
              width={width - 40}
              height={220}
              chartConfig={{
                backgroundColor: '#ffffff',
                backgroundGradientFrom: '#ffffff',
                backgroundGradientTo: '#ffffff',
                decimalPlaces: 1,
                color: () => config.app.theme.primaryColor,
                labelColor: () => '#333333',
                style: {
                  borderRadius: 16,
                },
                propsForDots: {
                  r: '6',
                  strokeWidth: '2',
                  stroke: config.app.theme.primaryColor,
                },
              }}
              bezier
              style={styles.chart}
            />
          </View>
        </View>
        
        {/* Category Performance */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Category Performance</Text>
          <View style={styles.chartContainer}>
            <BarChart
              data={dashboardData?.categoryPerformance}
              width={width - 40}
              height={220}
              yAxisSuffix=""
              yAxisLabel=""
              chartConfig={{
                backgroundColor: '#ffffff',
                backgroundGradientFrom: '#ffffff',
                backgroundGradientTo: '#ffffff',
                decimalPlaces: 1,
                color: () => config.app.theme.secondaryColor,
                labelColor: () => '#333333',
                style: {
                  borderRadius: 16,
                },
              }}
              style={styles.chart}
            />
          </View>
        </View>
        
        {/* Alerts */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Alerts</Text>
          <View style={styles.alertsContainer}>
            {dashboardData?.alerts.map((alert) => (
              <TouchableOpacity 
                key={alert.id} 
                style={[
                  styles.alertItem,
                  alert.type === 'price' ? styles.priceAlert : styles.trendAlert
                ]}
                onPress={() => navigation.navigate('AlertDetails', { alertId: alert.id })}
              >
                <Text style={styles.alertTitle}>{alert.title}</Text>
                <Text style={styles.alertMessage}>{alert.message}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        
        {/* Sync Status */}
        {!isOnline && dataSyncService.getPendingCount() > 0 && (
          <View style={styles.syncStatusContainer}>
            <Text style={styles.syncStatusText}>
              {`${dataSyncService.getPendingCount()} items waiting to sync`}
            </Text>
            <TouchableOpacity
              style={styles.syncButton}
              onPress={() => dataSyncService.forceSyncNow()}
            >
              <Text style={styles.syncButtonText}>Sync Now</Text>
            </TouchableOpacity>
          </View>
        )}
        
        {/* Bottom padding for scrolling */}
        <View style={styles.bottomPadding} />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666666',
  },
  header: {
    backgroundColor: config.app.theme.primaryColor,
    paddingVertical: 15,
    paddingHorizontal: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  offlineBadge: {
    backgroundColor: '#ff6b6b',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  offlineText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  scrollView: {
    flex: 1,
  },
  errorContainer: {
    margin: 20,
    padding: 15,
    backgroundColor: '#ffebee',
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#f44336',
  },
  errorText: {
    color: '#d32f2f',
    fontSize: 14,
  },
  section: {
    marginHorizontal: 20,
    marginTop: 20,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333333',
  },
  recommendationsContainer: {
    marginBottom: 10,
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  recommendationContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  productImage: {
    width: 50,
    height: 50,
    borderRadius: 6,
    marginRight: 12,
  },
  productInfo: {
    flex: 1,
  },
  productName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333333',
  },
  productCategory: {
    fontSize: 14,
    color: '#666666',
    marginTop: 4,
  },
  scoreContainer: {
    backgroundColor: config.app.theme.primaryColor,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  scoreText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  viewAllButton: {
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 6,
    marginTop: 10,
  },
  viewAllText: {
    color: config.app.theme.primaryColor,
    fontWeight: '600',
    fontSize: 14,
  },
  chartContainer: {
    alignItems: 'center',
    marginVertical: 10,
  },
  chart: {
    borderRadius: 16,
  },
  alertsContainer: {
    marginBottom: 10,
  },
  alertItem: {
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
  },
  priceAlert: {
    backgroundColor: '#e0f7fa',
    borderLeftWidth: 4,
    borderLeftColor: '#00bcd4',
  },
  trendAlert: {
    backgroundColor: '#f9fbe7',
    borderLeftWidth: 4,
    borderLeftColor: '#cddc39',
  },
  alertTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 5,
    color: '#333333',
  },
  alertMessage: {
    fontSize: 14,
    color: '#666666',
  },
  syncStatusContainer: {
    margin: 20,
    padding: 15,
    backgroundColor: '#fff8e1',
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  syncStatusText: {
    fontSize: 14,
    color: '#ff8f00',
    flex: 1,
  },
  syncButton: {
    backgroundColor: '#ff9800',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 4,
  },
  syncButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 12,
  },
  bottomPadding: {
    height: 30,
  },
});

export default Dashboard; 