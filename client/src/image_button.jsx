import React from 'react';
import PropTypes from 'prop-types';
import Button from 'react-bootstrap/Button';


const defaultStyle = {
  margin: '10px',
  padding: '10px',
  textAlign: 'center',
  verticalAlign: 'middle',
};

const imageStyle = {
  margin: 'auto',
  maxWidth: '100%',
};

class ImageButton extends React.Component {

  static getDerivedStateFromProps(newProps) {
    return newProps;
  }

  constructor(props) {
    super(props);

    this.state = {
      disabled: props.disabled,
      name: props.name,
      src: props.src,
      style: props.style,
    };
    this.callback = props.onClick;
    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    this.callback({
      name: this.props.name,
    });
  }

  render() {
    return (
      <Button
        disabled={this.state.disabled}
        name={this.state.name}
        style={Object.assign({}, defaultStyle, this.state.style)}
        variant="outline-success"
        onClick={this.handleClick}
      >
        <img
          alt={this.state.name}
          src={this.state.src}
          style={imageStyle}
        />
      </Button>
    );
  }

}

ImageButton.propTypes = {
  disabled: PropTypes.bool,
  name: PropTypes.string,
  src: PropTypes.string,
  style: PropTypes.object,
  onClick: PropTypes.func,
};

ImageButton.defaultProps = {
  disabled: false,
  name: '',
  src: '',
  style: {},
  onClick: (args) => {
    return console.log(args);
  },
};

export default ImageButton;
