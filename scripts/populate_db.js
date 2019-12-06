const create_person = (idx) => ({
    "name" : `name${idx}`,
    "age" : idx,
    "balance" : idx,
    "email" : `name${idx}@yahoo.com`,
    "address" : `address${idx}`,
    "created_date" : new ISODate(),
    "last_modified_date" : new ISODate()
});

const create_all_persons = (number = 88) => {
    [...Array(number).keys()].map(i => db.people.save(create_person(i + 11)));
}

const migrate = (seq, index) => {
    print (seq._id);
    db.sequence.update({_id: seq._id}, {$set: {sequence_size: seq.sequence.length}})
};
