import React from 'react';
import PropTypes from 'prop-types';

import ImageButton from './image_button.jsx';


const containerStyle = {
  display: 'flex',
  textAlign: 'center',
};

const btnContainerStyle = {
  margin: 'auto',
  padding: '10px',
  height: '100%',
  maxWidth: '45%',
};

const btnStyle = {
  height: '100%',
  width: '100%',
};

class MainView extends React.Component {

  static getDerivedStateFromProps(newProps) {
    return newProps;
  }

  constructor(props) {
    super(props);
    this.state = {
      disabled: props.disabled,
      target1: props.target1,
      target2: props.target2,
    };

    this.callback = props.onSelect;
    this.handleSelect = this.handleSelect.bind(this);
  }

  handleSelect({name}) {
    const [
      winner,
      loser,
    ] = this.state.target1.id === Number(name) ?
      [
        this.state.target1.id,
        this.state.target2.id,
      ] :
      [
        this.state.target2.id,
        this.state.target1.id,
      ];
    this.callback({
      winner: winner,
      loser: loser,
    });
  }

  render() {
    return (
      <div style={containerStyle}>
        <div
          style={btnContainerStyle}
          title={this.state.target1.rate}
        >
          <ImageButton
            disabled={this.state.disabled}
            name={String(this.state.target1.id)}
            src={this.state.target1.src}
            style={btnStyle}
            onClick={this.handleSelect}
          />
        </div>
        <div
          style={btnContainerStyle}
          title={this.state.target2.rate}
        >
          <ImageButton
            disabled={this.state.disabled}
            name={String(this.state.target2.id)}
            src={this.state.target2.src}
            style={btnStyle}
            onClick={this.handleSelect}
          />
        </div>
      </div>
    );
  }

}

MainView.propTypes = {
  disabled: PropTypes.bool,
  target1: PropTypes.shape({
    id: PropTypes.number,
    rate: PropTypes.number,
    src: PropTypes.string,
  }),
  target2: PropTypes.shape({
    id: PropTypes.number,
    rate: PropTypes.number,
    src: PropTypes.string,
  }),
  onSelect: PropTypes.func,
};

MainView.defaultProps = {
  disabled: false,
  target1: {},
  target2: {},
  onSelect: (args) => {
    return console.log(args);
  },
};

export default MainView;
