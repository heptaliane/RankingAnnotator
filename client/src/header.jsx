import React from 'react';
import PropTypes from 'prop-types';
import ProgressBar from 'react-bootstrap/ProgressBar';
import Button from 'react-bootstrap/Button';


const percentMul = 100;

const containerStyle = {
  display: 'flex',
  background: '#1f3134',
  padding: '20px',
};

const progressStyle = {
  width: '90%',
  margin: 'auto',
};

class Header extends React.Component {

  static getDerivedStateFromProps(newProps) {
    return newProps;
  }

  constructor(props) {
    super(props);

    this.state = {
      total: props.total,
      now: props.now,
    };

    this.callback = props.onClick;
    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    this.callback();
  }

  render() {
    return (
      <div style={containerStyle}>
        <div
          style={progressStyle}
          title={`${this.state.now} / ${this.state.total}`}
        >
          <ProgressBar
            animated={true}
            label={`${this.state.now / this.state.total * percentMul} %`}
            max={this.state.total}
            now={this.state.now}
          />
        </div>
        <Button
          onClick={this.handleClick}
        >
          undo
        </Button>
      </div>
    );
  }

}

Header.propTypes = {
  now: PropTypes.number,
  total: PropTypes.number,
  onClick: PropTypes.func,
};

Header.defaultProps = {
  now: 0,
  total: 1,
  onClick: () => {
    // Nothing to do
  },
};

export default Header;
