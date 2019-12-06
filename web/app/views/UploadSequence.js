import React from "react";
import Button from "react-bootstrap/Button";
import history from "../history";
import TableComponent from "../component/TableComponent";
import axios from "axios";

import {Progress} from 'react-sweet-progress';
import "react-sweet-progress/lib/style.css";

class UploadSequence extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            loading: true,
            canUpload: true
        }
    }

    getUpload = () => {
        this.setState({loading: true}, () => {
            axios.get('/api/sequence/upload')
                .then((response) => {
                    if (response.status === 200)
                        this.setState({loading: false, canUpload: true});

                    if (response.status === 206) {
                        this.setState({loading: false, canUpload: false, job: response.data});
                        setTimeout(() => this.getUpload(), 2500);
                    }

                }, (error) => {
                    console.log(error);
                });
        })
    }

    postUpload = () => {
        const formData = new FormData();
        formData.append('file', this.state.file);
        this.setState({loading: true});

        axios.post('/api/sequence/upload', formData, {
            headers: {
                'content-type': 'multipart/form-data'
            }
        }).then((result) => {
            this.getUpload();
        }, () => {
            this.getUpload();
        });
    };

    componentDidMount() {
        this.getUpload();
    }

    render() {
        return <div className="container" style={{marginTop: 75, marginBottom: 250}}>
            <div className='mb-5 flex d-flex align-items-center flex-row'>
                <div className='d-flex'>
                    <Button variant="primary" onClick={() => history.push('/')}>Back</Button>
                </div>
                <h1 className='ml-3'>{'Upload Sequence'}</h1>
            </div>

            {!this.state.canUpload && <div class="d-flex flex-column align-items-center justify-content-center">
                <h1 class="mb-5 mt-4">{'Upload currently in progress !'}</h1>
                <Progress percent={this.state.job?.percent || 10}/>
                <h3 class="mt-3">{this.state.job.message}</h3>
            </div>}
            {this.state.canUpload && <div class="row">
                <div class="column col-12">
                    <div className="form-group files">
                        <label>Upload Your File </label>
                        <input type="file" className="form-control" multiple=""
                               onChange={(e) => this.setState({file: e.target.files[0]})}/>
                    </div>
                    <button disabled={!this.state.file} type="button" class="btn btn-success flex"
                            onClick={this.postUpload}>Upload
                    </button>
                </div>
            </div>}
            {this.state.loading && <div className={'overlay loading'}/>}
        </div>
    }
}

export default UploadSequence;
