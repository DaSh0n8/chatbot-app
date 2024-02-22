import React, { useState, useEffect, useRef } from 'react';
import ChatBot from 'react-simple-chatbot';
import {Segment} from 'semantic-ui-react';
import axios from 'axios';
import botAvatar from './vitroxlogo.png';

// push
const Classifier = ({ steps }) => {
  const [responseMessage, setResponseMessage] = useState('');
  const [isHtmlResponse, setIsHtmlResponse] = useState(false);

  const handleApiResponse = (data, prefix, timeFrame) => {
    const { machine, oee } = data;
    const timeMappings = {
      week: 'this week',
      month: 'this month',
      today: 'today'
    };
    
    const time = timeMappings[timeFrame] || 'today';
    setIsHtmlResponse(false);
    setResponseMessage(`${prefix} machine ${time} is ${machine} with an OEE of ${oee}%`);
  };

  const handleError = (error, prefix) => {
    console.error(`Error fetching the ${prefix} machine:`, error);
    setIsHtmlResponse(false);
    setResponseMessage(`Sorry, I couldn't retrieve the ${prefix} machine.`);
  };

  const apiRequest = (endpoint, timeFrame, prefix) => {
    axios.post(`http://localhost:5000/${endpoint}`, { time_frame: timeFrame })
      .then(response => handleApiResponse(response.data, prefix, timeFrame))
      .catch(error => handleError(error, prefix));
  };

  const classificationActions = {
    best_machine_today: () => apiRequest('retrieve_best_machine', 'today', 'The best performing'),
    best_machine_month: () => apiRequest('retrieve_best_machine', 'month', 'The best performing'),
    best_machine_week: () => apiRequest('retrieve_best_machine', 'week', 'The best performing'),
    worst_machine_today: () => apiRequest('retrieve_worst_machine', 'today', 'The worst performing'),
    worst_machine_month: () => apiRequest('retrieve_worst_machine', 'month', 'The worst performing'),
    worst_machine_week: () => apiRequest('retrieve_worst_machine', 'week', 'The worst performing'),
    best_employee_week: () => setResponseMessage('The best employee this week is Brandon with a personal score of 80%.'),
    worst_employee_week: () => setResponseMessage('The worst employee this week is Brandon with a personal score of 10%.'),
    best_employee_month: () => setResponseMessage('The best employee this month is Brandon with a personal score of 80%.'),
    worst_employee_month: () => setResponseMessage('The worst employee this month is Brandon with a personal score of 10%.'),
    sales_report_week: () => {
      setIsHtmlResponse(true);
      setResponseMessage(`Download the sales report: <a href="/path/to/dummypdf.pdf" download="dummypdf.pdf">Click here</a>`);
    },
    Ambiguous: () => setResponseMessage("Sorry, I didn't quite catch that.")
  };

  useEffect(() => {
    const userResponse = steps.UserPrompt.value;
    axios.post('http://localhost:5000/predict', { sentence: userResponse })
      .then(response => {
        const classification = response.data.class;
        classificationActions[classification]?.();
      })
      .catch(error => {
        console.error("Error fetching classification:", error);
        setResponseMessage("Sorry, I couldn't get the classification.");
      });
  }, [steps.UserPrompt.value]);
  return isHtmlResponse ? <div dangerouslySetInnerHTML={{ __html: responseMessage }} /> : <div>{responseMessage}</div>;
};

function App() {

    const steps = [
      {
        id: 'Greet',
        message: 'Hello, how may I assist you today?',
        trigger: 'UserPrompt',
      },
      {
        id: 'UserPrompt',
        user: true,
        trigger: 'Classify'
      },
      {
        id: 'Classify',
        component: <Classifier />,
        trigger: 'FollowUp'
      },
      {
        id: 'FollowUp',
        message: 'Anything else I can help you with?',
        trigger: 'ConfirmMoreQuestions',
      },
      {
        id: "ConfirmMoreQuestions",
        options: [
          { value: "Yes", label: "Yes", trigger: "UserPrompt" }, 
          { value: "No", label: "No", trigger: "Goodbye" } 
        ]
      },
      {
        id: "Goodbye",
        message: "Bye",
        end: true
      }
      
    ];

    return (
      <Segment floated="right">
        <ChatBot key="unique-chatbot-key" recognitionEnable={true} steps={steps} botAvatar={botAvatar}/>
      </Segment>
    );
    
}

export default App;