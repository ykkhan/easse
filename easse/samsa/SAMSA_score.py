from easse.samsa.scene_sentence_extraction import get_scenes, get_sentences, get_ucca_passage
from easse.samsa.scene_sentence_alignment import align_scenes_sentences


def get_num_scenes(ucca_passage):
    """
    Returns the number of scenes in the ucca_passage.
    """
    scenes = [x for x in ucca_passage.layer("1").all if x.tag == "FN" and x.is_scene()]
    return len(scenes)


def get_num_sentences(text):
    return len(get_sentences(text))


def get_cmrelations(P):
    """
    P is a ucca passage. Return all the most internal centers of main relations in each passage
    """
    scenes = [x for x in P.layer("1").all if x.tag == "FN" and x.is_scene()]
    m = []
    for sc in scenes:
        mrelations = [e.child for e in sc.outgoing if e.tag == 'P' or e.tag == 'S']
        for mr in mrelations:
            centers = [e.child for e in mr.outgoing if e.tag == 'C']
            if centers:
                while centers:
                    for c in centers:
                        ccenters = [e.child for e in c.outgoing if e.tag == 'C']
                    lcenters = centers
                    centers = ccenters
                m.append(lcenters)
            else:
                m.append(mrelations)

    y = P.layer("0")
    output = []
    for scp in m:
        for par in scp:
            output2 =[]
            p = []
            d = par.get_terminals(False,True)
            for i in list(range(0,len(d))):
                p.append(d[i].position)

            for k in p:

                if(len(output2)) == 0:
                    output2.append(str(y.by_position(k)))
                elif str(y.by_position(k)) != output2[-1]:
                    output2.append(str(y.by_position(k)))

        output.append(output2)

    return(output)


def get_cparticipants(P):
    """
    P is a ucca passage. Return all the minimal participant centers in each scene
    """
    scenes = [x for x in P.layer("1").all if x.tag == "FN" and x.is_scene()]
    n = []
    for sc in scenes:  #find participant nodes
        m = []
        participants = [e.child for e in sc.outgoing if e.tag == 'A']
        for pa in participants:
            centers = [e.child for e in pa.outgoing if e.tag == 'C' ]
            if centers != []:
                while centers != []:
                    for c in centers:
                        ccenters = [e.child for e in c.outgoing if e.tag == 'C' or e.tag =='P' or e.tag =='S']   #also addresses center Scenes
                    lcenters = centers
                    centers = ccenters
                m.append(lcenters)
            elif pa.is_scene():  # address the case of Participant Scenes
                scenters = [e.child for e in pa.outgoing if e.tag == 'P' or e.tag == 'S']
                for scc in scenters:
                    centers = [e.child for e in scc.outgoing if e.tag == 'C']
                    if centers != []:
                        while centers != []:
                            for c in centers:
                                ccenters = [e.child for e in c.outgoing if e.tag == 'C']
                            lcenters = centers
                            centers = ccenters
                        m.append(lcenters)
                    else:
                        m.append(scenters)
            elif any(e.tag == "H" for e in pa.outgoing):  # address the case of multiple parallel Scenes inside a participant
                hscenes = [e.child for e in pa.outgoing if e.tag == 'H']
                mh = []
                for h in hscenes:
                    hrelations = [e.child for e in h.outgoing if e.tag == 'P' or e.tag == 'S']  # in case of multiple parallel scenes we generate new multiple centers
                    for hr in hrelations:
                        centers = [e.child for e in hr.outgoing if e.tag == 'C']
                        if centers != []:
                            while centers != []:
                                for c in centers:
                                    ccenters = [e.child for e in c.outgoing if e.tag == 'C']
                                lcenters = centers
                                centers = ccenters
                            mh.append(lcenters[0])
                        else:
                            mh.append(hrelations[0])
                m.append(mh)
            else:
                m.append([pa])

        n.append(m)

    y = P.layer("0")  # find cases of multiple centers
    output = []
    s = []
    I = []
    for scp in n:
        r = []
        u = n.index(scp)
        for par in scp:
            if len(par) > 1:
                d = scp.index(par)
                par = [par[i:i+1] for i in range(0,len(par))]
                for c in par:
                    r.append(c)
                I.append([u,d])
            else:
                r.append(par)
        s.append(r)

    for scp in s:  # find the spans of the participant nodes
        output1 = []
        for [par] in scp:
            output2 =[]
            p = []
            d = par.get_terminals(False,True)
            for i in list(range(0,len(d))):
                p.append(d[i].position)

            for k in p:

                if(len(output2)) == 0:
                    output2.append(str(y.by_position(k)))
                elif str(y.by_position(k)) != output2[-1]:
                    output2.append(str(y.by_position(k)))
            output1.append(output2)
        output.append(output1)

    y = []  # unify spans in case of multiple centers
    for scp in output:
        x = []
        u = output.index(scp)
        for par in scp:
            for v in I:
                if par == output[v[0]][v[1]]:
                    for l in list(range(1,len(n[v[0]][v[1]]))):
                        par.append((output[v[0]][v[1]+l])[0])

                    x.append(par)
                elif all(par != output[v[0]][v[1]+l] for l in list(range(1,len(n[v[0]][v[1]])))):
                    x.append(par)
            if I == []:
                x.append(par)
        y.append(x)

    return y


def samsa_sentence(orig_sentence, sys_output):
    orig_scenes = get_scenes(orig_sentence)
    sys_sentences = get_sentences(sys_output)
    all_scenes_alignments = align_scenes_sentences(orig_scenes, sys_sentences)

    orig_ucca_passage = get_ucca_passage(orig_sentence)
    orig_num_scenes = get_num_scenes(orig_ucca_passage)
    sys_num_sents = len(sys_sentences)
    M1 = get_cmrelations(orig_ucca_passage)
    A1 = get_cparticipants(orig_ucca_passage)

    if orig_num_scenes < sys_num_sents:
        score = 0.0
    elif orig_num_scenes == sys_num_sents:
        t = all_scenes_alignments

        match = []
        for i in range(orig_num_scenes):
            match_value = 0
            for j in range(sys_num_sents):
                if len(t[i][j]) > match_value and j not in match:
                    match_value = len(t[i][j])
                    m = j
            match.append(m)

        scorem = []
        scorea = []
        for i in range(orig_num_scenes):
            j = match[i]
            r = [t[i][j][k][0] for k in range(len(t[i][j]))]
            if M1[i]==[]:
               s = 0.5
            elif all(M1[i][l] in r for l in range(len(M1[i]))):
               s = 1
            else:
               s = 0
            scorem.append(s)
            sa = []
            if A1[i] == []:
                sa = [0.5]
                scorea.append(sa)
            else:
                for a in A1[i]:
                    if a == []:
                        p = 0.5
                    elif all(a[l] in r for l in range(len(a))):
                        p = 1
                    else:
                        p = 0
                    sa.append(p)
                scorea.append(sa)

        scoresc = []
        for i in range(orig_num_scenes):
            d = len(scorea[i])
            v = 0.5*scorem[i] + 0.5*(1/d)*sum(scorea[i])
            scoresc.append(v)
        score = (sys_num_sents/(orig_num_scenes**2))*sum(scoresc)
    else:
        t = all_scenes_alignments
        match = []
        for i in range(orig_num_scenes):
            match_value = 0
            for j in range(sys_num_sents):
                if len(t[i][j]) > match_value:
                    match_value = len(t[i][j])
                    m = j
            match.append(m)

        scorem = []
        scorea = []
        for i in range(orig_num_scenes):
            j = match[i]
            r = [t[i][j][k][0] for k in range(len(t[i][j]))]
            if M1[i]==[]:
                s = 0.5
            elif all(M1[i][l] in r for l in range(len(M1[i]))):
                s = 1
            else:
                s = 0
            scorem.append(s)
            sa = []
            if A1[i] == []:
                sa = [0.5]
                scorea.append(sa)
            else:
                for a in A1[i]:
                    if a == []:
                        p = 0.5
                    elif all(a[l] in r for l in range(len(a))):
                        p = 1
                    else:
                        p = 0
                    sa.append(p)
                scorea.append(sa)

        scoresc = []
        for i in range(orig_num_scenes):
            d = len(scorea[i])
            v = 0.5*scorem[i] + 0.5*(1/d)*sum(scorea[i])
            scoresc.append(v)
        score = (sys_num_sents/(orig_num_scenes**2))*sum(scoresc)
    return score
