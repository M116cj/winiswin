import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class LSTMModel(nn.Module):
    def __init__(self, input_size=5, hidden_size=64, num_layers=2, output_size=1):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

class LSTMPredictor:
    def __init__(self, lookback=50):
        self.lookback = lookback
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"LSTM Predictor initialized with device: {self.device}")
    
    def prepare_data(self, df):
        features = ['close', 'volume', 'macd', 'rsi', 'atr']
        
        df_clean = df[features].dropna()
        
        if len(df_clean) < self.lookback + 10:
            logger.error(f"Insufficient data after removing NaN: {len(df_clean)} rows")
            return None, None
        
        data = df_clean.values
        scaled_data = self.scaler.fit_transform(data)
        
        X, y = [], []
        for i in range(self.lookback, len(scaled_data)):
            X.append(scaled_data[i-self.lookback:i])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y)
    
    def train(self, df, epochs=50, batch_size=32):
        try:
            logger.info("Starting LSTM model training...")
            
            X, y = self.prepare_data(df)
            
            if X is None or y is None:
                logger.error("Data preparation failed")
                return False
            
            if len(X) < 10:
                logger.warning("Insufficient data for training")
                return False
            
            X_tensor = torch.FloatTensor(X).to(self.device)
            y_tensor = torch.FloatTensor(y).unsqueeze(1).to(self.device)
            
            train_size = int(0.8 * len(X))
            X_train, X_test = X_tensor[:train_size], X_tensor[train_size:]
            y_train, y_test = y_tensor[:train_size], y_tensor[train_size:]
            
            self.model = LSTMModel(input_size=X.shape[2]).to(self.device)
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
            
            self.model.train()
            for epoch in range(epochs):
                total_loss = 0
                for i in range(0, len(X_train), batch_size):
                    batch_X = X_train[i:i+batch_size]
                    batch_y = y_train[i:i+batch_size]
                    
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {total_loss/len(X_train):.6f}")
            
            self.model.eval()
            with torch.no_grad():
                test_outputs = self.model(X_test)
                test_loss = criterion(test_outputs, y_test)
                logger.info(f"Test Loss: {test_loss.item():.6f}")
            
            self.is_trained = True
            logger.info("LSTM model training completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error training LSTM model: {e}")
            return False
    
    def predict(self, df):
        if not self.is_trained or self.model is None:
            logger.warning("Model not trained yet")
            return None
        
        try:
            features = ['close', 'volume', 'macd', 'rsi', 'atr']
            df_clean = df[features].dropna()
            
            if len(df_clean) < self.lookback:
                logger.error(f"Insufficient clean data for prediction: {len(df_clean)} rows")
                return None
            
            data = df_clean.values[-self.lookback:]
            
            if np.isnan(data).any():
                logger.error("NaN values detected in prediction data")
                return None
            
            scaled_data = self.scaler.transform(data)
            X = torch.FloatTensor(scaled_data).unsqueeze(0).to(self.device)
            
            self.model.eval()
            with torch.no_grad():
                prediction_scaled = self.model(X).cpu().numpy()[0, 0]
            
            dummy = np.zeros((1, len(features)))
            dummy[0, 0] = prediction_scaled
            prediction = self.scaler.inverse_transform(dummy)[0, 0]
            
            current_price = df.iloc[-1]['close']
            price_change_percent = ((prediction - current_price) / current_price) * 100
            
            logger.info(f"LSTM Prediction: {prediction:.2f} (Change: {price_change_percent:+.2f}%)")
            
            return {
                'predicted_price': prediction,
                'current_price': current_price,
                'price_change_percent': price_change_percent,
                'direction': 'UP' if price_change_percent > 0 else 'DOWN'
            }
        
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return None
