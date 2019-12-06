import React from "react";
import axios from "axios";
import {Button} from "react-bootstrap";

import history from '../history';
import {editDistance, range} from "../utils/Utils";
import Select from "react-select";

class SequenceViewer extends React.Component {
    render() {
        const seqviz = window.seqviz;

        console.log(this.props);

        const {
            //part = "abcasdasdsadsadsadsadsadsa",
            backbone = "",
            view = "both",
            annotate = true,
            annotations = true,
            primers = true,
            complement = false,
            index = true,
            query = "",
            enzymes = [],
            lzoom = 50,
            setDemoState
        } = this.props;

        let part = null;

        if (this.props.item)
            part = {
                name: this.props.item.sequence_id,
                seq: this.props.item.sequence,
                annotations: [
                    // {
                    //     start: 133,
                    //     end: 457,
                    //     direction: "REVERSE",
                    //     name: "lacZ fragment",
                    //     color: "#8FDE8C",
                    //     type: "CDS"
                    // }
                ]
            };
        const viewer = seqviz.Viewer("root", {
            part: part,
            backbone: backbone,
            viewer: view,
            annotate: annotate,
            showAnnotations: annotations,
            showPrimers: primers,
            showComplement: complement,
            showIndex: index,
            zoom: {linear: lzoom},
            // onSelection: selection => {
            //     setDemoState({ selection: selection });
            // },
            // onSearch: results => {
            //     setDemoState({ searchResults: results });
            // },
            searchQuery: {query: query},
            copySeq: {
                key: "c",
                meta: true,
                ctrl: false,
                shift: false,
                alt: false
            },
            // enzymes: Object.values(enzymes)
        });

        return part && viewer.viewer;
    }
}

class SimilarSequence extends React.Component {
    render() {
        const {item, sequence} = this.props;

        console.log('start');
        console.log(sequence);
        console.log(item.sequence);

        const [s1, mid, s2] = editDistance(sequence, item.sequence);

        console.log(s1);
        console.log(mid);
        console.log(s2);

        return <div className="mt-4">
            <div className="flex-row col-12 mt-1 d-flex align-items-center ">
                <h2> - Name {item?.sequence_id}</h2>
                <Button className={'ml-2'} variant="primary"
                        onClick={() => history.push(`/sequence/${item.sequence_id}`)}>View</Button>
            </div>
            <div className="column col-12 mt-1">
                <h4>Details</h4>
                <div>{item?.tags}</div>
            </div>
            <div className="column col-12 mt-1">
                <h4>Sequence {item?.sequence_size}bp</h4>
                <div>Edit distance {item?.distance}</div>

                <div class="mt-3">
                    {range(0, s1.length, 60).map(start => {
                        let to = Math.min(start + 60, s1.length);

                        return <div style={{
                            fontFamily: 'Courier New,Courier,Lucida Sans Typewriter,Lucida Typewriter,monospace',
                            whiteSpace: 'pre'
                        }} class="mt-1">
                            <span style={{
                                letterSpacing: '2px',
                                display: 'block'
                            }}> {start.toString().padStart(10, " ")} {s1.substring(start, to).padEnd(60, " ")} {to.toString()} </span>
                            <span style={{
                                letterSpacing: '2px',
                                display: 'block'
                            }}> {" ".padStart(10, " ")} {mid.substring(start, to).padEnd(60, " ")}</span>
                            <span style={{
                                letterSpacing: '2px',
                                display: 'block'
                            }}> {" ".padStart(10, " ")} {s2.substring(start, to).padEnd(60, " ")}</span>
                        </div>
                    })}
                </div>
            </div>
        </div>
    }
}

class SequenceInfo extends React.Component {
    state = {
        distance: 100,
        loading: true,
        loadingSimilar: false
    }

    componentDidMount() {
        console.log(this.props.match);
        this.loadSequence();
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (this.props.match.params.id !== prevProps.match.params.id)
            this.loadSequence();
    }

    loadSequence = () => {
        this._id = this.props.match.params.id;

        axios.get('/api/crud/sequence', {params: {just_one: true, _query: {sequence_id: this._id}}})
            .then((response) => {
                window.scrollTo(0, 0);
                this.setState({loading: false, loadingSimilar: true, item: response.data}, () => this.getSimilar());
            }, () => {
            });

    };

    getSimilar = () => {
        axios.post('/api/sequence/query', {seq: this.state.item.sequence, dist: this.state.distance})
            .then((response) => {
                this.setState({
                    loadingSimilar: false,
                    similar: response.data.filter(item => item.sequence_id !== this.state.item.sequence_id)
                })
            }, () => {
            })
    };


    render() {
        const options = [
            {value: 25, label: '25'},
            {value: 50, label: '50'},
            {value: 100, label: '100'},
            {value: 150, label: '150'},
            {value: 200, label: '200'}
        ]

        return <div className="container" style={{marginTop: 75, marginBottom: 250}}>
            <div className='mb-5 flex d-flex align-items-center flex-row'>
                <div className='d-flex'>
                    <Button variant="primary" onClick={() => history.push('/')}>Back</Button>
                </div>
                <h1 className='ml-3'>{'Sequence Info ' + this._id}</h1>
            </div>

            <div class="row">
                <div class="column col-12">
                    <h2>Details</h2>
                    <div>{this.state?.item?.tags}</div>
                </div>
            </div>

            <div className="seqviewer">
                <h2>Sequence</h2>
                <SequenceViewer item={this.state.item}/>
            </div>

            <div style={{marginTop: '80px'}}>
                <div className="column col-12">
                    <h2>Similar sequences</h2>
                    <div>
                        <div>Max edit distance:</div>
                        <Select
                            disabled={this.state.loadingSimilar}
                            options={options} value={options.filter(option => option.value === this.state.distance)}
                            onChange={(value, action) => this.setState({distance: value.value, loadingSimilar: true}, () => this.getSimilar())}/>
                    </div>
                    <p>Total count: {this.state.similar && this.state.similar.length}</p>


                </div>
                {this.state.similar && this.state.similar.map(item => <SimilarSequence
                    sequence={this.state.item.sequence} item={item}/>)}
            </div>
            {(this.state.loading || this.state.loadingSimilar) && <div className={'overlay loading'}/>}
        </div>

    }
}

export default SequenceInfo;
