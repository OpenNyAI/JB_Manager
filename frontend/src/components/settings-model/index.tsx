import React, { useState, useEffect } from 'react';
import './settings-model.css';
import { sendRequest } from '@/api';
import { fetchSecret } from '@/pages/home/home';

interface InputConfig {
  value: string | number | boolean;
  is_secret?: boolean;
  type: 'string' | 'number' | 'boolean' | 'list' | 'text';
  placeholder?: string;
  required: boolean;
}

interface Props {
  title?: string;
  isOpen: boolean;
  onClose: () => void;
  inputs: Record<string, InputConfig>;
  bot_id: string;
  onSave: (inputs: Record<string, InputConfig>) => void;
  modelType: string;
  botId?: string;
}

const SettingsModal: React.FC<Props> = ({ botId, isOpen, onClose, inputs, modelType, title }) => {
  const [inputElements, setInputElements] = useState<Record<string, InputConfig>>({});
  const APIHOST = import.meta.env.VITE_SERVER_HOST;

  useEffect(() => {
    setInputElements(inputs || {});
  }, [inputs]);

  const updateValue = (key: string, newValue: string | number | boolean) => {
    setInputElements(prevState => ({
      ...prevState,
      [key]: {
        ...prevState[key],
        value: newValue,
      },
    }));
  };

  const getInputType = (inputConfig: InputConfig): string => {
    if (inputConfig.is_secret) return 'password';
    return inputConfig.type === 'number' ? 'number' : 'text'; // Expand as needed
  };

  const handleSubmit = async () => {
    let data:any = {};
    let apiEndpoint = '';
    let accessToken = null;
    if (modelType === 'credentials') {
        apiEndpoint = `${APIHOST}/v1/bot/${botId}/configure`;
        let credentials:any = {};
        for (let key in inputElements) {
          if (inputElements[key].required === true && !inputElements[key].value.toString().trim()) {
            alert(`${key} is required`);
            return;
          }
          credentials[key] = inputElements[key].value;
        }
        data['credentials'] = { ...credentials };
    } else if (modelType === 'activate') {
        apiEndpoint = `${APIHOST}/v1/bot/${botId}/activate`;
        if (inputElements['phone_number'].required === true && !inputElements['phone_number'].value.toString().trim()) {
            alert('Phone number is required');
            return;
        }
        if (inputElements['whatsapp'].required === true && !inputElements['whatsapp'].value.toString().trim()) {
            alert('Whatsapp Key is required');
            return;
        }
        data['phone_number'] = inputElements['phone_number'].value;
        data['channels'] = {};
        data['channels']['whatsapp'] = inputElements['whatsapp'].value;
    } else if (modelType === 'install') {
        apiEndpoint = `${APIHOST}/v1/bot/install`;
        try {
          accessToken = await fetchSecret();
      } catch (error) {
          console.error("Failed to fetch the access token:", error);
          alert("Failed to fetch the access token");
          return;
      }
        for (let key in inputElements) {
          if (inputElements[key].required === true && !inputElements[key].value.toString().trim()) {
            alert(`${key} is required`);
            return;
          }
          if (inputElements[key].type === 'list') {
            data[key] = inputElements[key].value.toString().split(',').map((item: string) => item.trim());
            continue;
          }
          data[key] = inputElements[key].value;
        }
    }
    try {
      await sendRequest({
        url: apiEndpoint,
        method: 'POST',
        accessToken: accessToken,
        body: JSON.stringify(data ),
        headers: {
            'Content-Type': 'application/json',
        }
      })
        onClose();
    } catch (error: any) {
        alert(`Error from server "${error?.body?.detail}". Please try again.`)
        console.error('Error saving settings:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="modal-overlay" onClick={onClose} />
      <div className="modal-container">
        <div className="modal-header">
          <h2>{title ? title : 'Settings'}</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {Object.keys(inputElements).map((key) => (
            <div className="input-wrapper" key={key}>
              <label>{key}{inputElements[key]?.required === true? ' *' : ''}</label>
              {inputElements[key].type === 'text' ?
                <textarea
                    className='text-area'
                    value={inputElements[key].value.toString()}
                    placeholder={inputElements[key].placeholder || ''}
                    onChange={e => updateValue(key, e.target.value)}
                    rows={5}
                />
              :
              <input
              type={getInputType(inputElements[key])}
                value={inputElements[key].value.toString()}
                placeholder={inputElements[key].placeholder || ''}
                onChange={e => updateValue(key, e.target.type === 'number' ? Number(e.target.value) : e.target.value)}
              />}
            </div>
          ))}
        </div>
        <div className="modal-footer">
          <button className="save-button" onClick={handleSubmit}>Save</button>
          <button className="cancel-button" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </>
  );
};

export default SettingsModal;
