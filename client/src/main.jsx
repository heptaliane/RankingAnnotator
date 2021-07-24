import React from 'react';
import {render} from 'react-dom';

import MainView from './main_view.jsx';
import Header from './header.jsx';

import 'bootstrap/dist/css/bootstrap.min.css';


class App extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
      disabled: true,
      total: 1,
      now: 0,
      target1: {},
      target2: {},
    };

    this.handleSelect = this.handleSelect.bind(this);
    this.handleUndo = this.handleUndo.bind(this);
    this.websocket = null;
  }

  componentDidMount() {
    this.websocket = new WebSocket(`ws://${location.host}/ws`);

    this.websocket.onmessage = (res) => {
      const data = JSON.parse(res.data);
      this.setState({
        disabled: false,
        now: data.matches.finished,
        total: data.matches.total,
        target1: data.target[0],
        target2: data.target[1],
      });
    };
  }

  handleSelect({winner, loser}) {
    if (!this.state.disabled) {
      this.setState({
        disabled: true,
        target1: {},
        target2: {},
      });
      this.websocket.send(JSON.stringify({
        action: 'select',
        loser: loser,
        winner: winner,
      }));
    }
  }

  handleUndo() {
    if (!this.state.disabled) {
      this.setState({
        disabled: true,
        target1: {},
        target2: {},
      });
      this.websocket.send(JSON.stringify({
        action: 'undo',
      }));
    }
  }

  render() {
    return (
      <div>
        <Header
          now={this.state.now}
          total={this.state.total}
          onClick={this.state.handleUndo}
        />
        <MainView
          target1={this.state.target1}
          target2={this.state.target2}
          onSelect={this.handleSelect}
        />
      </div>
    );
  }

}

render(
  <App />,
  document.getElementById('container'),
);
