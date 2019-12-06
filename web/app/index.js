import "@babel/polyfill";

import React from 'react'
import ReactDOM from 'react-dom'

import history from './history';
import {Router, Route, Switch, Redirect} from 'react-router-dom'
import Home from "./views/Home";

import 'font-awesome/css/font-awesome.min.css';
import 'bootstrap/dist/css/bootstrap.min.css';

import '../assets/scss/index.scss';
import Person from "./views/Person";
import Sequence from "./views/Sequence";
import UploadSequence from "./views/UploadSequence";
import SequenceInfo from "./views/SequenceInfo";

let render = () => {
    ReactDOM.render(
        <Router history={history}>
            <Switch>
                <Route path="/sequence/upload" component={UploadSequence}/>
                <Route path="/sequence/:id" component={SequenceInfo}/>
                <Route path="/" component={Sequence}/>
            </Switch>
        </Router>,
        document.getElementById('root')
    )
};

render()

// registerServiceWorker();
